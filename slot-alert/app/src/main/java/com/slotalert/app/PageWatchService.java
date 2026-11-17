package com.slotalert.app;

import android.app.AlarmManager;
import android.app.Notification;
import android.app.PendingIntent;
import android.app.Service;
import android.content.Context;
import android.content.Intent;
import android.content.pm.ServiceInfo;
import android.os.Build;
import android.os.Handler;
import android.os.IBinder;
import android.os.Looper;
import android.os.PowerManager;
import android.os.SystemClock;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebView;
import android.webkit.WebViewClient;

import org.json.JSONTokener;

import java.util.ArrayList;
import java.util.List;

/** Foreground service that opens each watched page in a hidden browser and compares the text near the watched place. */
public class PageWatchService extends Service {
    static final String ACTION_CHECK_NOW = "com.slotalert.app.CHECK_NOW";
    static final String ACTION_TICK = "com.slotalert.app.TICK";
    private static final int FG_ID = 1;
    private static final long PAGE_TIMEOUT_MS = 45_000;
    private static final long SETTLE_MS = 6_000;

    private final Handler h = new Handler(Looper.getMainLooper());
    private boolean running = false;
    private long lastRun = 0;
    private List<String> queue = new ArrayList<>();
    private WebView web;
    private boolean pageDone;
    private PowerManager.WakeLock wake;
    private final Runnable tick = () -> maybeCheck(false);

    static void startIfEnabled(Context c) {
        if (!Prefs.on(c, Prefs.PAGES_ON, false)) return;
        if (urls(c).isEmpty()) return;
        try {
            c.startForegroundService(new Intent(c, PageWatchService.class));
        } catch (Exception e) {
            Prefs.log(c, "Could not start page watching: " + e.getMessage());
        }
    }

    static void checkNow(Context c) {
        try {
            c.startForegroundService(new Intent(c, PageWatchService.class).setAction(ACTION_CHECK_NOW));
        } catch (Exception e) {
            Prefs.log(c, "Could not start page check: " + e.getMessage());
        }
    }

    static void stop(Context c) {
        c.stopService(new Intent(c, PageWatchService.class));
    }

    static List<String> urls(Context c) {
        List<String> out = new ArrayList<>();
        for (String l : Prefs.get(c, Prefs.URLS, "").split("\\s+")) {
            String u = l.trim();
            if (u.startsWith("http://") || u.startsWith("https://")) out.add(u);
        }
        return out;
    }

    @Override
    public IBinder onBind(Intent intent) { return null; }

    @Override
    public int onStartCommand(Intent intent, int flags, int startId) {
        Alerts.channels(this);
        int n = urls(this).size();
        Notification note = new Notification.Builder(this, Alerts.CH_STATUS)
                .setSmallIcon(R.drawable.ic_bell)
                .setContentTitle("Slot Alert is watching " + n + (n == 1 ? " page" : " pages"))
                .setContentText("Checks every " + Prefs.interval(this) + " minutes")
                .setOngoing(true)
                .setContentIntent(PendingIntent.getActivity(this, 3, new Intent(this, MainActivity.class),
                        PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE))
                .build();
        try {
            if (Build.VERSION.SDK_INT >= 34) {
                startForeground(FG_ID, note, ServiceInfo.FOREGROUND_SERVICE_TYPE_SPECIAL_USE);
            } else {
                startForeground(FG_ID, note);
            }
        } catch (Exception e) {
            Prefs.log(this, "Android blocked background watching: " + e.getMessage());
            stopSelf();
            return START_NOT_STICKY;
        }
        boolean manual = intent != null && ACTION_CHECK_NOW.equals(intent.getAction());
        if (!manual && (!Prefs.on(this, Prefs.PAGES_ON, false) || n == 0)) {
            stopSelf();
            return START_NOT_STICKY;
        }
        maybeCheck(manual);
        return START_STICKY;
    }

    private long intervalMs() { return Prefs.interval(this) * 60_000L; }

    private void scheduleNext() {
        h.removeCallbacks(tick);
        if (!Prefs.on(this, Prefs.PAGES_ON, false)) return;
        h.postDelayed(tick, intervalMs());
        // Backup wake-up for when the phone is dozing and the timer above is held back.
        try {
            PendingIntent pi = PendingIntent.getForegroundService(this, 4,
                    new Intent(this, PageWatchService.class).setAction(ACTION_TICK),
                    PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
            getSystemService(AlarmManager.class).setAndAllowWhileIdle(AlarmManager.ELAPSED_REALTIME_WAKEUP,
                    SystemClock.elapsedRealtime() + intervalMs() + 30_000, pi);
        } catch (Exception ignored) { }
    }

    private void maybeCheck(boolean force) {
        if (running) return;
        long now = SystemClock.elapsedRealtime();
        if (!force && lastRun != 0 && now - lastRun < intervalMs() * 8 / 10) {
            scheduleNext();
            return;
        }
        queue = urls(this);
        if (queue.isEmpty()) {
            Prefs.log(this, "No pages to check — add a page address first");
            finishRun();
            return;
        }
        running = true;
        lastRun = now;
        try {
            wake = getSystemService(PowerManager.class).newWakeLock(PowerManager.PARTIAL_WAKE_LOCK, "slotalert:check");
            wake.acquire(queue.size() * (PAGE_TIMEOUT_MS + 5_000));
        } catch (Exception ignored) { }
        next();
    }

    private void next() {
        destroyWeb();
        if (queue.isEmpty()) {
            finishRun();
            return;
        }
        final String url = queue.remove(0);
        pageDone = false;
        try {
            web = new WebView(getApplicationContext());
            web.getSettings().setJavaScriptEnabled(true);
            web.getSettings().setDomStorageEnabled(true);
            web.setWebViewClient(new WebViewClient() {
                private boolean scheduled = false;

                @Override
                public void onPageFinished(WebView v, String u) {
                    if (scheduled) return;
                    scheduled = true;
                    h.postDelayed(() -> read(v, url), SETTLE_MS);
                }

                @Override
                public void onReceivedError(WebView v, WebResourceRequest req, WebResourceError err) {
                    if (req != null && req.isForMainFrame()) {
                        done(v, url, null, "could not load (" + err.getDescription() + ")");
                    }
                }
            });
            final WebView mine = web;
            h.postDelayed(() -> done(mine, url, null, "timed out"), PAGE_TIMEOUT_MS);
            web.loadUrl(url);
        } catch (Exception e) {
            Prefs.log(this, host(url) + ": hidden browser failed — " + e.getMessage());
            h.post(this::next);
        }
    }

    private void read(WebView v, String url) {
        if (v != web || pageDone) return;
        try {
            v.evaluateJavascript("(function(){return document.body?document.body.innerText:'';})()", value -> {
                String text = "";
                try {
                    Object o = new JSONTokener(value == null ? "\"\"" : value).nextValue();
                    if (o instanceof String) text = (String) o;
                } catch (Exception ignored) { }
                done(v, url, text, null);
            });
        } catch (Exception e) {
            done(v, url, null, "could not read page");
        }
    }

    private void done(WebView v, String url, String text, String error) {
        if (v != web || pageDone) return;
        pageDone = true;
        try {
            if (error != null) {
                Prefs.log(this, host(url) + ": " + error);
            } else {
                evaluate(url, text);
            }
        } catch (Exception e) {
            Prefs.log(this, host(url) + ": error — " + e);
        }
        h.post(this::next);
    }

    private void evaluate(String url, String text) {
        String places = Prefs.get(this, Prefs.PLACES, Prefs.DEF_PLACES);
        String snip = Logic.snippets(text, places, 60, 220);
        String key = "seen:" + url;
        if (snip.isEmpty()) {
            Prefs.log(this, host(url) + ": page loaded (" + Logic.collapse(text).length()
                    + " characters) but none of your places are mentioned");
            return;
        }
        String norm = Logic.normalize(snip);
        String old = Prefs.sp(this).getString(key, null);
        Prefs.sp(this).edit().putString(key, norm).apply();
        boolean quiet = Logic.containsAny(snip, Logic.words(Prefs.get(this, Prefs.QUIET, Prefs.DEF_QUIET)));
        if (old == null) {
            Prefs.log(this, host(url) + ": first look saved — " + clip(snip));
        } else if (old.equals(norm)) {
            Prefs.log(this, host(url) + ": no change");
        } else if (quiet) {
            Prefs.log(this, host(url) + ": changed but still says no slots — " + clip(snip));
        } else {
            Alerts.fire(this, "p:" + url + norm.hashCode(), "Page changed: " + host(url), snip);
        }
    }

    private static String clip(String s) { return s.length() > 140 ? s.substring(0, 140) + "…" : s; }

    private static String host(String url) {
        try {
            String hst = android.net.Uri.parse(url).getHost();
            return hst == null ? url : hst;
        } catch (Exception e) {
            return url;
        }
    }

    private void destroyWeb() {
        if (web != null) {
            try { web.stopLoading(); web.destroy(); } catch (Exception ignored) { }
            web = null;
        }
    }

    private void finishRun() {
        running = false;
        try { if (wake != null && wake.isHeld()) wake.release(); } catch (Exception ignored) { }
        wake = null;
        if (Prefs.on(this, Prefs.PAGES_ON, false) && !urls(this).isEmpty()) {
            scheduleNext();
        } else {
            stopSelf();
        }
    }

    @Override
    public void onDestroy() {
        h.removeCallbacksAndMessages(null);
        destroyWeb();
        try { if (wake != null && wake.isHeld()) wake.release(); } catch (Exception ignored) { }
        super.onDestroy();
    }
}
