package com.slotalert.app;

import android.Manifest;
import android.app.Activity;
import android.app.NotificationManager;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.graphics.Typeface;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.os.PowerManager;
import android.provider.Settings;
import android.text.InputType;
import android.view.View;
import android.widget.Button;
import android.widget.CheckBox;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import android.widget.Toast;

public class MainActivity extends Activity {
    private static final int GREEN = 0xFF1B7F3B, RED = 0xFFB3261E, GREY = 0xFF555555;
    private LinearLayout root;
    private TextView stNotif, stAccess, stBattery, logView;
    private EditText places, topics, urls, interval, quiet, bookUrl;
    private CheckBox notifOn, pagesOn, insistent;
    private final Handler h = new Handler(Looper.getMainLooper());
    private final SharedPreferences.OnSharedPreferenceChangeListener logListener =
            (sp, key) -> { if (Prefs.LOG.equals(key)) h.post(this::showLog); };

    @Override
    protected void onCreate(Bundle b) {
        super.onCreate(b);
        Alerts.channels(this);
        ScrollView sv = new ScrollView(this);
        root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        int p = dp(16);
        root.setPadding(p, p, p, dp(48));
        sv.addView(root);
        setContentView(sv);

        text("Get a loud alarm the moment a visa-slot message for your consulate reaches this phone.", 15, GREY, false);

        head("Step 1 · Let this app show alerts");
        stNotif = text("", 14, GREY, true);
        steps("Tap the button, then tap Allow.");
        button("Allow alerts", v -> askNotifications());

        head("Step 2 · Let this app read notifications");
        stAccess = text("", 14, GREY, true);
        steps("This is how the app hears about slots: it reads notifications from apps like CheckVisaSlots, Telegram and X, and sounds the alarm when one mentions your consulate.\n"
                + "1. Tap “Open notification access”.\n"
                + "2. Find Slot Alert in the list and switch it on, then tap Allow.\n"
                + "If the switch is greyed out or you see “Restricted setting”:\n"
                + "a. Tap “Open app info” below.\n"
                + "b. Tap the ⋮ menu at the top right, then “Allow restricted settings”.\n"
                + "c. Come back and repeat steps 1 and 2.");
        button("Open notification access", v -> open(new Intent(Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS)));
        button("Open app info", v -> openAppInfo());

        head("Step 3 · Keep the app running in the background");
        stBattery = text("", 14, GREY, true);
        steps("Tap the button, then tap Allow. On Xiaomi, Oppo, Vivo, Realme and OnePlus phones also open app info, then turn on Autostart and set Battery to “No restrictions”.");
        button("Allow background running", v -> askBattery());
        button("Open app info", v -> openAppInfo());

        head("Step 4 · Turn on the sources");
        steps("The alarm only rings when another app on this phone shows a matching notification. Set up at least one:\n"
                + "• CheckVisaSlots: turn on its alerts for H-1B.\n"
                + "• X: follow the two US Mission accounts below and tap the bell on each profile.\n"
                + "• Telegram: join a slot channel and leave its notifications on.");
        button("Open CheckVisaSlots", v -> openUrl("https://checkvisaslots.com/"));
        button("Open @USAndIndia on X", v -> openUrl("https://x.com/USAndIndia"));
        button("Open @USAndMumbai on X", v -> openUrl("https://x.com/USAndMumbai"));

        head("Step 5 · Test it");
        steps("Send a test alert. It should ring like an alarm even if the phone is on silent (not in Do Not Disturb unless you allow it in the alert settings).");
        button("Send test alert", v -> Alerts.fire(this, "test:" + System.currentTimeMillis(),
                "Test alert", "This is how a Mumbai H-1B slot alert will look and sound."));
        button("Alert sound and Do Not Disturb settings", v -> open(new Intent(Settings.ACTION_CHANNEL_NOTIFICATION_SETTINGS)
                .putExtra(Settings.EXTRA_APP_PACKAGE, getPackageName())
                .putExtra(Settings.EXTRA_CHANNEL_ID, Alerts.CH_ALERT)));

        head("What to listen for");
        notifOn = check("Watch notifications from other apps", Prefs.on(this, Prefs.NOTIF_ON, true));
        insistent = check("Keep ringing until I dismiss the alert", Prefs.on(this, Prefs.INSISTENT, true));
        label("Places (any one must appear)");
        places = field(Prefs.get(this, Prefs.PLACES, Prefs.DEF_PLACES), false);
        label("Topics (any one must appear)");
        topics = field(Prefs.get(this, Prefs.TOPICS, Prefs.DEF_TOPICS), false);
        label("Site to open when I tap an alert");
        bookUrl = field(Prefs.get(this, Prefs.BOOK_URL, Prefs.DEF_BOOK), false);

        head("Optional · Watch web pages too");
        steps("The app can also open public tracker pages itself and alert when the text next to your place changes. Paste one address per line. Do not use the official booking site here: it needs your login, and automated checks can get accounts suspended.");
        pagesOn = check("Watch these pages in the background", Prefs.on(this, Prefs.PAGES_ON, false));
        label("Page addresses (one per line)");
        urls = field(Prefs.get(this, Prefs.URLS, ""), true);
        label("Check every (minutes, 5 or more)");
        interval = field(String.valueOf(Prefs.interval(this)), false);
        interval.setInputType(InputType.TYPE_CLASS_NUMBER);
        label("Do not alert while the text still says");
        quiet = field(Prefs.get(this, Prefs.QUIET, Prefs.DEF_QUIET), false);

        button("Save settings", v -> { save(); toast("Saved"); });
        button("Check pages now", v -> { save(); PageWatchService.checkNow(this); toast("Checking — results appear in the activity list below"); });

        head("Activity");
        logView = text("", 13, GREY, false);
        button("Clear activity", v -> { Prefs.sp(this).edit().remove(Prefs.LOG).apply(); showLog(); });

        PageWatchService.startIfEnabled(this);
    }

    @Override
    protected void onResume() {
        super.onResume();
        refresh();
        showLog();
        Prefs.sp(this).registerOnSharedPreferenceChangeListener(logListener);
    }

    @Override
    protected void onPause() {
        Prefs.sp(this).unregisterOnSharedPreferenceChangeListener(logListener);
        super.onPause();
    }

    @Override
    public void onRequestPermissionsResult(int code, String[] perms, int[] results) {
        super.onRequestPermissionsResult(code, perms, results);
        refresh();
    }

    private void refresh() {
        boolean n = getSystemService(NotificationManager.class).areNotificationsEnabled();
        status(stNotif, n, "Alerts are allowed", "Alerts are not allowed yet");
        String listeners = Settings.Secure.getString(getContentResolver(), "enabled_notification_listeners");
        boolean a = listeners != null && listeners.contains(getPackageName() + "/");
        status(stAccess, a, "Notification access is on", "Notification access is off");
        boolean bt = getSystemService(PowerManager.class).isIgnoringBatteryOptimizations(getPackageName());
        status(stBattery, bt, "Background running is allowed", "Android may stop this app in the background");
    }

    private void status(TextView t, boolean ok, String yes, String no) {
        t.setText(ok ? "✓ " + yes : "✗ " + no);
        t.setTextColor(ok ? GREEN : RED);
    }

    private void showLog() {
        String log = Prefs.get(this, Prefs.LOG, "");
        logView.setText(log.isEmpty() ? "Nothing yet." : log);
    }

    private void save() {
        int mins = Prefs.DEF_INTERVAL;
        try { mins = Integer.parseInt(interval.getText().toString().trim()); } catch (Exception ignored) { }
        mins = Math.max(Prefs.MIN_INTERVAL, mins);
        interval.setText(String.valueOf(mins));
        Prefs.sp(this).edit()
                .putString(Prefs.PLACES, places.getText().toString())
                .putString(Prefs.TOPICS, topics.getText().toString())
                .putString(Prefs.QUIET, quiet.getText().toString())
                .putString(Prefs.URLS, urls.getText().toString())
                .putString(Prefs.BOOK_URL, bookUrl.getText().toString().trim())
                .putInt(Prefs.INTERVAL, mins)
                .putBoolean(Prefs.NOTIF_ON, notifOn.isChecked())
                .putBoolean(Prefs.INSISTENT, insistent.isChecked())
                .putBoolean(Prefs.PAGES_ON, pagesOn.isChecked())
                .apply();
        if (pagesOn.isChecked() && !PageWatchService.urls(this).isEmpty()) {
            PageWatchService.startIfEnabled(this);
        } else {
            PageWatchService.stop(this);
        }
    }

    private void askNotifications() {
        if (Build.VERSION.SDK_INT >= 33
                && checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED
                && shouldAsk()) {
            requestPermissions(new String[]{Manifest.permission.POST_NOTIFICATIONS}, 7);
        } else {
            open(new Intent(Settings.ACTION_APP_NOTIFICATION_SETTINGS)
                    .putExtra(Settings.EXTRA_APP_PACKAGE, getPackageName()));
        }
    }

    /** After two denials Android stops showing the prompt, so fall back to the settings page. */
    private boolean shouldAsk() {
        int asked = Prefs.sp(this).getInt("asked_notif", 0);
        Prefs.sp(this).edit().putInt("asked_notif", asked + 1).apply();
        return asked < 2;
    }

    private void askBattery() {
        if (getSystemService(PowerManager.class).isIgnoringBatteryOptimizations(getPackageName())) {
            toast("Already allowed");
            return;
        }
        try {
            startActivity(new Intent(Settings.ACTION_REQUEST_IGNORE_BATTERY_OPTIMIZATIONS,
                    Uri.parse("package:" + getPackageName())));
        } catch (Exception e) {
            open(new Intent(Settings.ACTION_IGNORE_BATTERY_OPTIMIZATION_SETTINGS));
        }
    }

    private void openAppInfo() {
        open(new Intent(Settings.ACTION_APPLICATION_DETAILS_SETTINGS, Uri.parse("package:" + getPackageName())));
    }

    private void openUrl(String url) { open(new Intent(Intent.ACTION_VIEW, Uri.parse(url))); }

    private void open(Intent i) {
        try {
            startActivity(i);
        } catch (Exception e) {
            toast("Could not open that screen on this phone");
        }
    }

    private void toast(String s) { Toast.makeText(this, s, Toast.LENGTH_LONG).show(); }

    private int dp(int v) { return Math.round(v * getResources().getDisplayMetrics().density); }

    private TextView text(String s, int sp, int color, boolean bold) {
        TextView t = new TextView(this);
        t.setText(s);
        t.setTextSize(sp);
        t.setTextColor(color);
        if (bold) t.setTypeface(Typeface.DEFAULT_BOLD);
        t.setPadding(0, dp(4), 0, dp(4));
        t.setTextIsSelectable(true);
        root.addView(t);
        return t;
    }

    private void head(String s) {
        TextView t = text(s, 18, 0xFF111111, true);
        t.setPadding(0, dp(24), 0, dp(4));
    }

    private void steps(String s) { text(s, 14, 0xFF333333, false); }

    private void label(String s) { text(s, 13, GREY, false).setPadding(0, dp(10), 0, 0); }

    private Button button(String s, View.OnClickListener l) {
        Button b = new Button(this);
        b.setText(s);
        b.setAllCaps(false);
        b.setOnClickListener(l);
        root.addView(b, new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT));
        return b;
    }

    private CheckBox check(String s, boolean on) {
        CheckBox c = new CheckBox(this);
        c.setText(s);
        c.setChecked(on);
        root.addView(c);
        return c;
    }

    private EditText field(String value, boolean multi) {
        EditText e = new EditText(this);
        e.setText(value);
        e.setTextSize(14);
        if (multi) {
            e.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_FLAG_MULTI_LINE | InputType.TYPE_TEXT_VARIATION_URI);
            e.setMinLines(3);
        } else {
            e.setInputType(InputType.TYPE_CLASS_TEXT | InputType.TYPE_TEXT_FLAG_NO_SUGGESTIONS);
        }
        root.addView(e, new LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT,
                LinearLayout.LayoutParams.WRAP_CONTENT));
        return e;
    }
}
