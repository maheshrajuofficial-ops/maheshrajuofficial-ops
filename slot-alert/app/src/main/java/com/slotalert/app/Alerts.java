package com.slotalert.app;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.content.Context;
import android.content.Intent;
import android.media.AudioAttributes;
import android.media.RingtoneManager;
import android.net.Uri;

final class Alerts {
    static final String CH_ALERT = "slot_alerts_v1";
    static final String CH_STATUS = "status_v1";
    private static String lastKey = "";
    private static long lastAt = 0;

    private Alerts() {}

    static void channels(Context c) {
        NotificationManager nm = c.getSystemService(NotificationManager.class);
        NotificationChannel a = new NotificationChannel(CH_ALERT, "Slot alerts", NotificationManager.IMPORTANCE_HIGH);
        a.setDescription("Loud alert when a watched place and visa topic show up");
        Uri sound = RingtoneManager.getDefaultUri(RingtoneManager.TYPE_ALARM);
        if (sound == null) sound = RingtoneManager.getDefaultUri(RingtoneManager.TYPE_NOTIFICATION);
        a.setSound(sound, new AudioAttributes.Builder()
                .setUsage(AudioAttributes.USAGE_ALARM)
                .setContentType(AudioAttributes.CONTENT_TYPE_SONIFICATION).build());
        a.enableVibration(true);
        a.setVibrationPattern(new long[]{0, 600, 300, 600, 300, 900});
        a.setLockscreenVisibility(Notification.VISIBILITY_PUBLIC);
        nm.createNotificationChannel(a);
        NotificationChannel s = new NotificationChannel(CH_STATUS, "Background watching", NotificationManager.IMPORTANCE_LOW);
        s.setDescription("Silent notice shown while pages are being watched");
        nm.createNotificationChannel(s);
    }

    /** Fires the loud alert. The same key is not repeated within two minutes. */
    static synchronized void fire(Context c, String key, String title, String body) {
        long now = System.currentTimeMillis();
        if (key.equals(lastKey) && now - lastAt < 120_000) return;
        lastKey = key;
        lastAt = now;
        channels(c);
        String url = Prefs.get(c, Prefs.BOOK_URL, Prefs.DEF_BOOK);
        Intent open;
        try {
            open = new Intent(Intent.ACTION_VIEW, Uri.parse(url));
        } catch (Exception e) {
            open = new Intent(c, MainActivity.class);
        }
        open.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
        PendingIntent book = PendingIntent.getActivity(c, 1, open,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        PendingIntent app = PendingIntent.getActivity(c, 2,
                new Intent(c, MainActivity.class).addFlags(Intent.FLAG_ACTIVITY_NEW_TASK),
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE);
        Notification n = new Notification.Builder(c, CH_ALERT)
                .setSmallIcon(R.drawable.ic_bell)
                .setContentTitle(title)
                .setContentText(body)
                .setStyle(new Notification.BigTextStyle().bigText(body))
                .setCategory(Notification.CATEGORY_ALARM)
                .setVisibility(Notification.VISIBILITY_PUBLIC)
                .setAutoCancel(true)
                .setContentIntent(book)
                .addAction(new Notification.Action.Builder(null, "Open booking site", book).build())
                .addAction(new Notification.Action.Builder(null, "Open Slot Alert", app).build())
                .build();
        if (Prefs.on(c, Prefs.INSISTENT, true)) n.flags |= Notification.FLAG_INSISTENT;
        c.getSystemService(NotificationManager.class).notify((int) (now % 100000) + 100, n);
        Prefs.log(c, "ALERT: " + title + " — " + (body.length() > 160 ? body.substring(0, 160) + "…" : body));
    }
}
