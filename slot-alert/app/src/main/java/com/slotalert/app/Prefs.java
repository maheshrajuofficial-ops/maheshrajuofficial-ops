package com.slotalert.app;

import android.content.Context;
import android.content.SharedPreferences;

import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.Locale;

final class Prefs {
    static final String PLACES = "places";
    static final String TOPICS = "topics";
    static final String QUIET = "quiet";
    static final String URLS = "urls";
    static final String INTERVAL = "interval";
    static final String PAGES_ON = "pages_on";
    static final String NOTIF_ON = "notif_on";
    static final String INSISTENT = "insistent";
    static final String BOOK_URL = "book_url";
    static final String LOG = "log";

    static final String DEF_PLACES = "mumbai, bombay";
    static final String DEF_TOPICS = "h1b, h-1b, h1-b, h 1b, slot, appointment";
    static final String DEF_QUIET = "no open dates, no slots, no dates, not available, no appointments, none available, n/a";
    static final String DEF_BOOK = "https://www.usvisascheduling.com/";
    static final int DEF_INTERVAL = 10;
    static final int MIN_INTERVAL = 5;

    private Prefs() {}

    static SharedPreferences sp(Context c) {
        return c.getApplicationContext().getSharedPreferences("slotalert", Context.MODE_PRIVATE);
    }

    static String get(Context c, String key, String def) { return sp(c).getString(key, def); }
    static boolean on(Context c, String key, boolean def) { return sp(c).getBoolean(key, def); }

    static int interval(Context c) {
        return Math.max(MIN_INTERVAL, sp(c).getInt(INTERVAL, DEF_INTERVAL));
    }

    static synchronized void log(Context c, String msg) {
        String stamp = new SimpleDateFormat("dd MMM HH:mm", Locale.US).format(new Date());
        String old = sp(c).getString(LOG, "");
        String[] lines = old.isEmpty() ? new String[0] : old.split("\n");
        StringBuilder sb = new StringBuilder(stamp + "  " + msg.replace('\n', ' '));
        for (int i = 0; i < lines.length && i < 59; i++) sb.append('\n').append(lines[i]);
        sp(c).edit().putString(LOG, sb.toString()).apply();
    }
}
