package com.slotalert.app;

import android.app.Notification;
import android.content.pm.PackageManager;
import android.os.Bundle;
import android.os.Parcelable;
import android.service.notification.NotificationListenerService;
import android.service.notification.StatusBarNotification;

/** Reads other apps' notifications and raises a loud alert when one mentions a watched place and topic. */
public class NotifWatcher extends NotificationListenerService {

    @Override
    public void onNotificationPosted(StatusBarNotification sbn) {
        try {
            if (sbn == null || getPackageName().equals(sbn.getPackageName())) return;
            if (!Prefs.on(this, Prefs.NOTIF_ON, true)) return;
            Notification n = sbn.getNotification();
            if (n == null || (n.flags & Notification.FLAG_GROUP_SUMMARY) != 0) return;
            String text = textOf(n);
            if (text.isEmpty()) return;
            if (!Logic.matches(text,
                    Prefs.get(this, Prefs.PLACES, Prefs.DEF_PLACES),
                    Prefs.get(this, Prefs.TOPICS, Prefs.DEF_TOPICS))) return;
            Alerts.fire(this, "n:" + text.hashCode(), "Slot alert from " + appName(sbn.getPackageName()), text);
        } catch (Exception e) {
            Prefs.log(this, "Notification watcher error: " + e);
        }
    }

    private static void add(StringBuilder sb, CharSequence cs) {
        if (cs == null) return;
        String s = cs.toString().trim();
        if (!s.isEmpty() && sb.indexOf(s) < 0) sb.append(sb.length() > 0 ? " | " : "").append(s);
    }

    static String textOf(Notification n) {
        StringBuilder sb = new StringBuilder();
        Bundle x = n.extras;
        if (x != null) {
            add(sb, x.getCharSequence(Notification.EXTRA_TITLE));
            add(sb, x.getCharSequence(Notification.EXTRA_TEXT));
            add(sb, x.getCharSequence(Notification.EXTRA_BIG_TEXT));
            add(sb, x.getCharSequence(Notification.EXTRA_SUB_TEXT));
            CharSequence[] lines = x.getCharSequenceArray(Notification.EXTRA_TEXT_LINES);
            if (lines != null) for (CharSequence l : lines) add(sb, l);
            Parcelable[] msgs = x.getParcelableArray(Notification.EXTRA_MESSAGES);
            if (msgs != null) {
                for (int i = Math.max(0, msgs.length - 3); i < msgs.length; i++) {
                    if (msgs[i] instanceof Bundle) add(sb, ((Bundle) msgs[i]).getCharSequence("text"));
                }
            }
        }
        if (n.tickerText != null) add(sb, n.tickerText);
        return sb.toString();
    }

    private String appName(String pkg) {
        try {
            PackageManager pm = getPackageManager();
            return pm.getApplicationLabel(pm.getApplicationInfo(pkg, 0)).toString();
        } catch (Exception e) {
            return pkg;
        }
    }
}
