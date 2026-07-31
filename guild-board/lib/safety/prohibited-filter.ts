/**
 * Prohibited-task filter.
 *
 * Runs on every task submission before it reaches the board. Three outcomes:
 *
 *   block   — the submission is refused outright and never written.
 *   review  — the task is written but held back from the board
 *             (`requires_admin_review`) until a human clears it.
 *   allow   — published immediately.
 *
 * Two things this deliberately is not: it is not a moderation system on its
 * own (a human queue and user reports are the other two legs), and it is not
 * tuned for recall at any cost. A filter that blocks "help me move a gun
 * cabinet" trains people to write around it. Ambiguous matches go to `review`,
 * and only unambiguous ones block.
 *
 * Every rule carries an `exceptions` list because that is where the false
 * positives actually live — "glue gun", "nail gun", "bar tender", "hot tub
 * wiring question". Add to them freely; add to the block patterns carefully.
 */

import type { SafetyCategory, SafetyMatch, SafetyVerdict } from '@/types/api';
import type { RiskTier } from '@/types/database';

type Action = 'allow' | 'review' | 'block';

interface Rule {
  name: string;
  category: SafetyCategory;
  action: Action;
  patterns: RegExp[];
  /** If any of these match, the rule does not fire. */
  exceptions?: RegExp[];
  /** Licence slug the worker must hold when this rule fires. */
  requiresLicence?: string;
  /** Copy shown to the poster. */
  message: string;
}

/* -------------------------------------------------------------------------- */
/* Normalisation                                                              */
/* -------------------------------------------------------------------------- */

const LEET: Record<string, string> = {
  '0': 'o',
  '1': 'i',
  '3': 'e',
  '4': 'a',
  '5': 's',
  '7': 't',
  '@': 'a',
  $: 's',
  '!': 'i',
};

/**
 * Fold the text into a comparable form: lowercase, de-accented, leetspeak
 * resolved, and separator characters between single letters removed so that
 * `g.u.n` and `c-o-c-a-i-n-e` collapse to the plain word.
 */
export function normalizeForScan(input: string): string {
  const deAccented = input
    .normalize('NFKD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase();

  const deLeet = deAccented.replace(/[01345789@$!]/g, (ch) => LEET[ch] ?? ch);

  // Collapse single-letter separations: "g u n" / "g.u.n" -> "gun".
  //
  // The run happily starts on a preceding one-letter word, so "a c-o-c-a-i-n-e"
  // would collapse to "acocaine" and slip past every \b-anchored rule. When the
  // run opens with an article followed by whitespace, keep that letter separate.
  const deSpaced = deLeet.replace(/\b(?:[a-z][^a-z0-9]{1,2}){2,}[a-z]\b/g, (run) => {
    const letters = run.replace(/[^a-z]/g, '');
    return /^[ai]\s/.test(run) ? `${run[0]} ${letters.slice(1)}` : letters;
  });

  return deSpaced.replace(/\s+/g, ' ').trim();
}

/* -------------------------------------------------------------------------- */
/* Rules                                                                      */
/* -------------------------------------------------------------------------- */

const RULES: Rule[] = [
  /* --- Hard blocks -------------------------------------------------------- */
  {
    name: 'controlled_substances',
    category: 'controlled_substances',
    action: 'block',
    patterns: [
      /\b(cocaine|heroin|fentanyl|meth(amphetamine)?|mdma|ketamine|lsd)\b/,
      /\b(deliver|drop\s?off|pick\s?up|courier|transport|move|sell|source|score)\b[^.!?]{0,40}\b(weed|cannabis|marijuana|pills|oxy|adderall|xanax|percocet)\b/,
      /\b(unmarked|discreet|no\s?questions)\b[^.!?]{0,30}\b(package|parcel|delivery|drop)\b/,
      /\b(grow\s?op|trap\s?house|plug|re-?up)\b/,
    ],
    exceptions: [
      /\b(dispensary|licensed|prescription\s+pick\s?up|pharmacy)\b/,
      /\b(weed(ing|er)?\s+(the\s+)?(garden|yard|lawn|beds?|flower))\b/,
      /\bpull\s+weeds\b/,
    ],
    message:
      'Tasks involving controlled substances cannot be posted on Guild Board.',
  },
  {
    name: 'weapons',
    category: 'weapons',
    action: 'block',
    patterns: [
      /\b(firearm|handgun|shotgun|rifle|ammunition|ammo|silencer|suppressor)\b[^.!?]{0,40}\b(buy|sell|transport|deliver|acquire|source|modif|convert|build)\b/,
      /\b(buy|sell|transport|deliver|acquire|source|modify|convert|build)\b[^.!?]{0,40}\b(firearm|handgun|shotgun|rifle|ammunition|ammo|silencer|suppressor)\b/,
      /\b(ghost\s?gun|auto\s?sear|switch\s?for\s+a?\s?glock|serial\s+number\s+(removal|filed))\b/,
      /\b(explosive|pipe\s?bomb|molotov|thermite|det\s?cord)\b/,
    ],
    exceptions: [
      /\b(glue|nail|staple|caulk|heat|spray|paint|grease|water|foam|squirt)\s?gun\b/,
      /\b(gun\s?(safe|cabinet|case|rack|locker))\b/,
      /\bnerf\b/,
      /\b(airsoft|paintball)\s+(field|arena|party|event)\b/,
    ],
    message: 'Tasks involving weapons, ammunition or explosives are prohibited.',
  },
  {
    name: 'sexual_services',
    category: 'sexual_services',
    action: 'block',
    patterns: [
      /\b(escort|sugar\s?(baby|daddy)|sexual\s+(services?|favou?rs?)|erotic\s+massage|happy\s+ending)\b/,
      /\b(companionship)\b[^.!?]{0,30}\b(intimate|overnight|discreet)\b/,
      /\b(onlyfans|nudes?)\b[^.!?]{0,30}\b(shoot|content|film|record)\b/,
    ],
    exceptions: [
      /\b(elder|senior|companion)\s+(care|sitting|visit)\b/,
      /\bmassage\s+therapist\b[^.!?]{0,30}\blicensed\b/,
    ],
    message: 'Guild Board does not host tasks involving sexual services.',
  },
  {
    name: 'minors',
    category: 'minors',
    action: 'block',
    patterns: [
      /\b(child|kid|minor|teen(ager)?|under\s?1[0-7]|1[0-5]\s?(year|yr)s?\s?old)\b[^.!?]{0,50}\b(labou?r|work\s+shift|construction|demolition|roofing|night\s+shift|hazardous)\b/,
      /\b(hire|need|looking\s+for)\b[^.!?]{0,20}\b(under\s?1[0-7]|minors?)\b/,
    ],
    message:
      'Tasks that would put a minor to work cannot be posted. Babysitting and childcare belong under Pet & Home care with an adult worker.',
  },
  {
    name: 'financial_fraud',
    category: 'financial_fraud',
    action: 'block',
    patterns: [
      /\b(launder|money\s?mule|cash\s?out\s+(stolen|hacked)|fake\s+(id|passport|licen[cs]e|diploma|invoice))\b/,
      /\b(chargeback|refund)\s+(scam|scheme|exploit)\b/,
      /\b(open|use)\b[^.!?]{0,30}\b(bank\s+account|card)\b[^.!?]{0,30}\b(my\s+name|your\s+name|on\s+behalf)\b[^.!?]{0,30}\b(cash|transfer|wire)\b/,
      /\b(crypto|bitcoin|usdt)\b[^.!?]{0,30}\b(mule|cash\s?out|mix(er|ing))\b/,
      /\b(write|complete|sit)\b[^.!?]{0,30}\b(my\s+)?(exam|dissertation|thesis|coursework)\b[^.!?]{0,20}\b(for\s+me|on\s+my\s+behalf)\b/,
    ],
    exceptions: [/\bbookkeep(ing|er)\b/, /\binvoice\s+(entry|data|filing|chasing)\b/],
    message:
      'Tasks involving fraud, forged documents or moving money on someone else’s behalf are prohibited.',
  },
  {
    name: 'privacy_violation',
    category: 'privacy_violation',
    action: 'block',
    patterns: [
      /\b(follow|track|tail|surveil|stake\s?out|find\s+the\s+address\s+of)\b[^.!?]{0,40}\b(my\s+)?(ex|girlfriend|boyfriend|wife|husband|partner|neighbou?r|someone)\b/,
      /\b(install|plant|hide)\b[^.!?]{0,30}\b(tracker|air\s?tag|gps|spyware|hidden\s+camera|keylogger)\b[^.!?]{0,40}\b(their|his|her|someone\s?else)/,
      /\b(hack|break\s+into|get\s+into)\b[^.!?]{0,30}\b(account|phone|email|instagram|facebook|wifi)\b/,
      /\b(serve|deliver)\b[^.!?]{0,20}\b(papers)\b[^.!?]{0,30}\b(without|avoid|trick)\b/,
    ],
    exceptions: [
      /\b(install|set\s?up)\b[^.!?]{0,30}\b(my|our)\b[^.!?]{0,20}\b(security\s+camera|doorbell|ring|nest)\b/,
      /\bfind\s+my\s+(own\s+)?(lost|missing)\b/,
    ],
    message:
      'Tasks involving surveillance of another person, or unauthorised access to their accounts or devices, are prohibited.',
  },
  {
    name: 'illegal_general',
    category: 'illegal',
    action: 'block',
    patterns: [
      /\b(break\s+in|pick\s+(a\s+)?lock)\b[^.!?]{0,40}\b(not\s+my|someone\s?else|their|neighbou?r)\b/,
      /\b(dispose|dump|get\s+rid)\b[^.!?]{0,30}\b(body|remains|corpse)\b/,
      /\b(illegal(ly)?|off\s+the\s+books|under\s+the\s+table)\b[^.!?]{0,30}\b(dump|dispose|evict|wire|connect|bypass)\b/,
      /\b(bypass|tamper\s+with|cut)\b[^.!?]{0,25}\b(meter|smart\s+meter|utility\s+seal)\b/,
      /\b(threaten|rough\s+up|scare|intimidate)\b[^.!?]{0,30}\b(tenant|neighbou?r|someone|him|her|them)\b/,
    ],
    exceptions: [
      /\block(ed)?\s+(myself|ourselves)\s+out\b/,
      /\block\s?smith\b[^.!?]{0,30}\bmy\s+(own\s+)?(home|house|flat|apartment|car)\b/,
    ],
    message: 'This task appears to describe an illegal activity.',
  },
  {
    name: 'platform_circumvention',
    category: 'platform_circumvention',
    action: 'review',
    patterns: [
      /\b(pay|paid|payment)\b[^.!?]{0,30}\b(cash\s+in\s+hand|off\s?[- ]?platform|outside\s+(the\s+)?(app|site|platform)|venmo|zelle|cash\s?app|paypal\s+friends)\b/,
      /\b(text|whats\s?app|telegram|signal|dm)\s+me\s+(at|on)?\s?\+?\d[\d\s().-]{7,}/,
      /\b(contact\s+me\s+directly|skip\s+the\s+fee|avoid\s+the\s+fee)\b/,
    ],
    message:
      'Arranging payment or contact off-platform removes escrow protection for both sides, so this task needs a quick review.',
  },

  /* --- Hazardous work: allowed, but flagged and priced as elevated risk ---- */
  {
    name: 'hazardous_work',
    category: 'hazardous',
    action: 'review',
    patterns: [
      /\b(asbestos|lead\s+paint\s+removal|black\s+mo(u)?ld\s+remediation|biohazard|sewage\s+backup|needle\s+disposal)\b/,
      /\b(confined\s+space|crawl\s?space\s+entry|trench|excavat(e|ion))\b/,
      /\b(chainsaw|tree\s+fell(ing)?|limb\s+removal)\b[^.!?]{0,30}\b(large|tall|near\s+(the\s+)?(house|power|line))\b/,
      /\b(roof|gutter|chimney|second\s+stor(e?y|ies)|third\s+floor)\b[^.!?]{0,30}\b(ladder|climb|scaffold)\b/,
      /\b(pressure\s+vessel|gas\s+(line|bottle|cylinder)|propane\s+tank|fuel\s+transfer)\b/,
      /\b(demolition|knock\s+down\s+(a\s+)?wall|load[- ]bearing)\b/,
    ],
    exceptions: [
      /\b(gutter|window)\s+clean(ing)?\b[^.!?]{0,20}\b(ground|single\s+stor(e?y)|from\s+below)\b/,
    ],
    message:
      'This looks like hazardous work. It stays on the board but is marked elevated-risk, and workers see the hazard notice before bidding.',
  },

  /* --- Licensed trades: review + licence requirement ---------------------- */
  {
    name: 'licensed_trade.electrical',
    category: 'licensed_trade',
    action: 'review',
    requiresLicence: 'electrical',
    patterns: [
      /\b(rewire|re-?wiring|wire\s+up|new\s+circuit|consumer\s+unit|breaker\s+(panel|box)|fuse\s?box|distribution\s+board)\b/,
      /\b(install|replace|move|add)\b[^.!?]{0,30}\b(outlet|socket|light\s+switch|ceiling\s+fan|light\s+fixture|ev\s+charger|sub\s?panel|junction\s+box)\b/,
      /\b(240\s?v|220\s?v|110\s?v|mains\s+(power|voltage)|three\s+phase)\b/,
      /\belectrical\s+(work|repair|fault|inspection)\b/,
    ],
    exceptions: [
      /\b(change|replace|swap)\b[^.!?]{0,20}\b(light\s?)?bulb\b/,
      /\b(plug\s?in|plugged\s?in)\b/,
      /\b(reset|flip)\b[^.!?]{0,15}\bbreaker\b/,
      /\bbattery\b[^.!?]{0,15}\b(smoke\s+alarm|detector)\b/,
    ],
    message:
      'Electrical work requires a licensed electrician. This task will publish once a licensed worker is matched — unlicensed bids are blocked automatically.',
  },
  {
    name: 'licensed_trade.plumbing',
    category: 'licensed_trade',
    action: 'review',
    requiresLicence: 'plumbing',
    patterns: [
      /\b(re-?pipe|repipe|water\s+(main|heater)\s+(install|replace)|sewer\s+line|soil\s+stack|back\s?flow\s+preventer)\b/,
      /\b(install|replace|move|reroute)\b[^.!?]{0,30}\b(toilet|shower|bath\s?tub|sink|dishwasher\s+line|washing\s+machine\s+valve|boiler|water\s+heater|radiator)\b/,
      /\b(gas\s+(line|fitting|appliance|hob|boiler))\b/,
      /\b(burst|leaking)\s+(pipe|main)\b/,
    ],
    exceptions: [
      /\b(unclog|unblock|plunge|snake)\b[^.!?]{0,20}\b(drain|toilet|sink)\b/,
      /\b(replace|change)\b[^.!?]{0,15}\b(washer|tap\s+aerator|shower\s+head|toilet\s+seat)\b/,
    ],
    message:
      'Plumbing and gas work requires a licensed plumber or gas-safe engineer. Unlicensed bids on this task are blocked automatically.',
  },
  {
    name: 'licensed_trade.hvac',
    category: 'licensed_trade',
    action: 'review',
    requiresLicence: 'hvac',
    patterns: [
      /\b(hvac|refrigerant|freon|r-?410a|heat\s+pump|furnace|ac\s+(unit|compressor|recharge)|air\s+conditioning\s+(install|repair|recharge))\b/,
      /\b(install|replace|service)\b[^.!?]{0,25}\b(boiler|flue|ductwork|mini\s?split)\b/,
    ],
    exceptions: [/\b(replace|change|clean)\b[^.!?]{0,20}\b(air\s+)?filter\b/],
    message:
      'HVAC and refrigerant work requires a certified technician. Unlicensed bids on this task are blocked automatically.',
  },
  {
    name: 'licensed_trade.roofing',
    category: 'licensed_trade',
    action: 'review',
    requiresLicence: 'roofing',
    patterns: [
      /\b(re-?roof|roof\s+(replacement|repair|tiles?|shingles?|flashing|membrane)|flat\s+roof|chimney\s+(repoint|rebuild)|scaffold(ing)?\s+(erect|hire))\b/,
      /\b(structural\s+(work|repair|alteration|change|survey|support|beam|wall)|load[- ]bearing|underpinning|rsj|steel\s+beam)\b/,
    ],
    exceptions: [/\b(clear|clean)\b[^.!?]{0,20}\bgutters?\b[^.!?]{0,25}\bsingle\s+stor(e?y)\b/],
    message:
      'Roofing, work at height and structural changes require a licensed and insured contractor.',
  },
  {
    name: 'licensed_trade.regulated_professional',
    category: 'licensed_trade',
    action: 'review',
    patterns: [
      /\b(prescri(be|ption)|inject|iv\s+drip|administer\s+(medication|meds)|wound\s+care|catheter|stitches|dental)\b/,
      /\b(legal\s+advice|represent\s+me\s+in\s+court|draft\s+(my\s+)?(will|contract)\s+for\s+filing|immigration\s+petition)\b/,
      /\b(file\s+my\s+taxes|tax\s+return|audit\s+representation|financial\s+advice|invest\s+my)\b/,
      /\b(therapy|counsel(l)?ing)\s+session\b/,
    ],
    exceptions: [
      /\b(pick\s?up|collect|drop\s?off)\b[^.!?]{0,25}\b(prescription|meds|medication)\b/,
      /\b(ride|lift|transport|drive)\b[^.!?]{0,25}\b(to\s+the\s+)?(doctor|dentist|clinic|hospital|appointment)\b/,
      /\b(organi[sz]e|sort|scan|file)\b[^.!?]{0,20}\b(paperwork|documents|receipts)\b/,
    ],
    message:
      'Medical, legal, tax and therapeutic services must come from a licensed professional. This task needs review before it goes live.',
  },
];

/* -------------------------------------------------------------------------- */
/* Evaluation                                                                 */
/* -------------------------------------------------------------------------- */

const ACTION_RANK: Record<Action, number> = { allow: 0, review: 1, block: 2 };

export interface ScanInput {
  title: string;
  description: string;
  /** Category the poster chose; a licensed category escalates on its own. */
  categorySlug?: string;
  categoryRequiresLicence?: boolean;
}

/**
 * Scan a submission and return the verdict the API layer acts on.
 *
 * Cheap and synchronous by design: it runs inline on every task write, and on
 * bid proposal text, where a round-trip to a moderation service would not be.
 */
export function scanTaskContent(input: ScanInput): SafetyVerdict {
  const haystack = normalizeForScan(`${input.title}\n${input.description}`);

  const matches: SafetyMatch[] = [];
  const requiredLicences = new Set<string>();
  let action: Action = 'allow';
  let message: string | null = null;

  for (const rule of RULES) {
    if (rule.exceptions?.some((exception) => exception.test(haystack))) continue;

    const hit = rule.patterns.find((pattern) => pattern.test(haystack));
    if (!hit) continue;

    matches.push({
      rule: rule.name,
      term: hit.exec(haystack)?.[0]?.slice(0, 120) ?? rule.name,
      category: rule.category,
    });

    if (rule.requiresLicence) requiredLicences.add(rule.requiresLicence);

    if (ACTION_RANK[rule.action] > ACTION_RANK[action]) {
      action = rule.action;
      message = rule.message;
    } else if (ACTION_RANK[rule.action] === ACTION_RANK[action] && !message) {
      message = rule.message;
    }
  }

  // The chosen category can require a licence even when the wording is clean —
  // someone posting under "Electrical" gets the licence gate regardless.
  if (input.categoryRequiresLicence && input.categorySlug) {
    requiredLicences.add(input.categorySlug);
    if (ACTION_RANK.review > ACTION_RANK[action]) {
      action = 'review';
      message =
        message ??
        'This category is restricted to licensed trades. Only workers with a verified licence can bid.';
    }
  }

  return {
    action,
    riskTier: deriveRiskTier(action, matches, requiredLicences.size > 0),
    matches,
    reason: action === 'allow' ? null : message,
    requiredLicences: [...requiredLicences],
  };
}

function deriveRiskTier(
  action: Action,
  matches: SafetyMatch[],
  needsLicence: boolean
): RiskTier {
  if (needsLicence) return 'high_licensed';
  if (action === 'block') return 'high_licensed';
  if (matches.some((m) => m.category === 'hazardous')) return 'medium';
  if (matches.length > 0) return 'medium';
  return 'low';
}

/**
 * Lighter scan for free-text that isn't a task: bid proposals, chat messages.
 * Only the hard-block and circumvention rules apply — a worker mentioning
 * "electrical" in a proposal is not a licensing event.
 */
export function scanFreeText(text: string): SafetyVerdict {
  const haystack = normalizeForScan(text);
  const matches: SafetyMatch[] = [];
  let action: Action = 'allow';
  let message: string | null = null;

  for (const rule of RULES) {
    if (rule.category === 'licensed_trade' || rule.category === 'hazardous') continue;
    if (rule.exceptions?.some((exception) => exception.test(haystack))) continue;

    const hit = rule.patterns.find((pattern) => pattern.test(haystack));
    if (!hit) continue;

    matches.push({
      rule: rule.name,
      term: hit.exec(haystack)?.[0]?.slice(0, 120) ?? rule.name,
      category: rule.category,
    });

    if (ACTION_RANK[rule.action] > ACTION_RANK[action]) {
      action = rule.action;
      message = rule.message;
    }
  }

  return {
    action,
    riskTier: action === 'allow' ? 'low' : 'medium',
    matches,
    reason: message,
    requiredLicences: [],
  };
}

/** Exposed for the admin review queue and for tests. */
export const SAFETY_RULES = RULES.map(({ name, category, action, message }) => ({
  name,
  category,
  action,
  message,
}));
