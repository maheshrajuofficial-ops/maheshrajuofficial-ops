package com.slotalert.app;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;

/** Pure text logic (no Android imports) so it can be tested on a desktop JVM. */
public final class Logic {
    private Logic() {}

    public static List<String> words(String csv) {
        List<String> out = new ArrayList<>();
        if (csv == null) return out;
        for (String w : csv.split("[,\\n]")) {
            String t = w.trim().toLowerCase(Locale.ROOT);
            if (!t.isEmpty()) out.add(t);
        }
        return out;
    }

    public static boolean containsAny(String text, List<String> words) {
        if (text == null) return false;
        String t = text.toLowerCase(Locale.ROOT);
        for (String w : words) if (t.contains(w)) return true;
        return false;
    }

    /** A notification matches when it names a watched place AND a watched topic. */
    public static boolean matches(String text, String placeCsv, String topicCsv) {
        List<String> places = words(placeCsv);
        List<String> topics = words(topicCsv);
        if (places.isEmpty() || topics.isEmpty()) return false;
        return containsAny(text, places) && containsAny(text, topics);
    }

    public static String collapse(String s) {
        return s == null ? "" : s.replaceAll("\\s+", " ").trim();
    }

    /** The text right around each mention of a watched place on a page. */
    public static String snippets(String pageText, String placeCsv, int before, int after) {
        String text = collapse(pageText);
        String lower = text.toLowerCase(Locale.ROOT);
        StringBuilder sb = new StringBuilder();
        int coveredTo = -1;
        int count = 0;
        for (String p : words(placeCsv)) {
            int from = 0;
            while (count < 12) {
                int i = lower.indexOf(p, from);
                if (i < 0) break;
                from = i + p.length();
                int s = Math.max(0, i - before);
                int e = Math.min(text.length(), i + p.length() + after);
                if (s < coveredTo) s = Math.min(coveredTo, e);
                if (e > s) {
                    if (sb.length() > 0) sb.append(" … ");
                    sb.append(text, s, e);
                    coveredTo = e;
                    count++;
                }
            }
        }
        return sb.toString();
    }

    /** Strips things that change on every visit (clock times, "5 min ago") so they do not look like news. */
    public static String normalize(String snippet) {
        String s = snippet.toLowerCase(Locale.ROOT);
        s = s.replaceAll("\\b\\d{1,2}:\\d{2}(:\\d{2})?\\s*(am|pm)?(\\s*(ist|utc|gmt|est|edt|pst|pdt|cst|cdt))?\\b", "");
        s = s.replaceAll("\\b(\\d+|an?|few)\\s*(s|sec|secs|second|seconds|m|min|mins|minute|minutes|h|hr|hrs|hour|hours|d|day|days)\\s*ago\\b", "");
        s = s.replaceAll("\\bjust now\\b|\\btoday\\b|\\byesterday\\b", "");
        // "last checked 11 Nov 2026" style stamps: drop the date that follows the label
        s = s.replaceAll("\\b(last\\s+)?(checked|check|updated|refreshed|as of|data entry)\\b[^a-z0-9]*(on|at)?[^a-z0-9]*(\\d{1,2}\\s+[a-z]{3,9}\\.?,?\\s+\\d{4}|[a-z]{3,9}\\.?\\s+\\d{1,2},?\\s+\\d{4}|\\d{1,4}[-/]\\d{1,2}[-/]\\d{1,4})?", "");
        return collapse(s);
    }
}
