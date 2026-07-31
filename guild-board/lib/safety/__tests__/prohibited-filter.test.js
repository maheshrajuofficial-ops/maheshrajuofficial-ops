/**
 * Safety filter cases.
 *
 * The first block is the one that matters: plausible, legitimate tasks that a
 * naive keyword filter would refuse. A filter that blocks "move a gun cabinet"
 * or "pull the weeds" teaches people to write around it, which is strictly
 * worse than letting it through and catching it in review.
 *
 *   npm run test:safety
 */
const { scanTaskContent, scanFreeText } = require('../../../.test-build/lib/safety/prohibited-filter.js');

const cases = [
  // --- must be ALLOWED (false-positive traps) ---
  ['allow', 'Help me move a gun cabinet down two flights', 'Heavy steel gun safe, empty, needs two people and a stair dolly for the move.'],
  ['allow', 'Weeding and general tidy-up of a small back garden', 'Pull weeds from the flower beds, trim the hedge, bag it all up and take it to the tip.'],
  ['allow', 'Replace two light bulbs in a high ceiling', 'I cannot reach the fitting in the stairwell. Bring a ladder, I have the bulbs already.'],
  ['allow', 'Unblock a kitchen sink drain', 'Slow draining for a week. Probably needs a plunge or a snake, nothing structural.'],
  ['allow', 'Need a hand with a glue gun for a craft stall', 'Assembling 200 party favours with a hot glue gun ahead of a market on Saturday.'],
  ['allow', 'Pick up my prescription from the pharmacy', 'Collect a repeat prescription from the chemist on the high street and drop it round.'],
  ['allow', 'Drive my mum to her dentist appointment', 'Round trip to the dental clinic on Thursday, she needs an arm to lean on but walks fine.'],
  ['allow', 'Install my new Ring doorbell', 'I have the doorbell and the chime, I just need someone to set it up and connect the app.'],
  ['allow', 'Change the air filter on my furnace', 'Standard 16x25 filter, I have a replacement, I just cannot reach the unit safely.'],
  ['allow', 'Reset the breaker after a power cut', 'The trip switch in the hall cupboard needs flipping back, I am away until Friday.'],

  // --- must be BLOCKED ---
  ['block', 'Discreet delivery, no questions asked', 'Need an unmarked package moved across town tonight, discreet delivery, no questions asked.'],
  ['block', 'Transport a rifle to a buyer across state lines', 'Need someone to deliver a rifle and ammunition to a buyer two states over this week.'],
  ['block', 'Track my ex girlfriend for a few days', 'I want someone to follow my ex girlfriend and tell me where she goes after work each day.'],
  ['block', 'Make me a fake ID for a night out', 'Need a fake id that scans properly, willing to pay well for a quick turnaround this week.'],
  ['block', 'Get into my colleague Instagram account', 'I need someone to hack an instagram account and send me the messages inside it.'],

  // --- must go to REVIEW with a licence requirement ---
  ['review', 'Replace the consumer unit in a two-bed flat', 'Old rewireable fuse box needs swapping for a modern RCBO board, with a certificate.', 'electrical'],
  ['review', 'Install a new water heater in the basement', 'Old unit is leaking and needs to be replaced, including the connections to the mains.', 'plumbing'],
  ['review', 'Re-roof a small garage', 'Felt roof is failing, needs stripping and a new membrane and flashing fitted properly.', 'roofing'],
  ['review', 'Recharge the AC in my flat', 'The air conditioning unit needs a refrigerant recharge before summer really gets going.', 'hvac'],
  ['review', 'Asbestos garage sheet removal', 'Old garage has corrugated asbestos cement sheets that need removing and disposing of.'],
];

let pass = 0, fail = 0;
for (const [expected, title, description, licence] of cases) {
  const v = scanTaskContent({ title, description });
  const okAction = v.action === expected;
  const okLicence = !licence || v.requiredLicences.includes(licence);
  if (okAction && okLicence) { pass++; }
  else {
    fail++;
    console.log(`FAIL [${expected}] "${title}"`);
    console.log(`     got action=${v.action} tier=${v.riskTier} licences=[${v.requiredLicences}] matches=${v.matches.map(m=>m.rule).join(',')}`);
  }
}

// Evasion handling
const evasion = scanTaskContent({ title: 'Need a c-o-c-a-i-n-e courier tonight', description: 'Discreet person needed for a quick run across town, cash paid on completion today.' });
if (evasion.action !== 'block') { console.log('FAIL evasion: spaced-out term not blocked'); fail++; } else { pass++; }

// Off-platform payment nudge should be review, not block
const offPlatform = scanFreeText('Pay me cash in hand and we can skip the fee, text me on 555 010 9988.');
if (offPlatform.action !== 'review') { console.log('FAIL off-platform nudge not flagged'); fail++; } else { pass++; }

console.log(`\nsafety filter: ${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
