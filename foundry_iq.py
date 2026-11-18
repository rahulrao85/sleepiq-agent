"""
Sleep IQ — Foundry IQ Medical Knowledge Grounding

Provides grounded medical knowledge retrieval for the AI agent.
Uses Azure AI Search if configured, otherwise falls back to an embedded
knowledge base of AASM guidelines, ResMed clinical recommendations,
and sleep medicine best practices.

Every answer includes a citation from a verifiable source.
"""

import json, os, re

# ─── Embedded Knowledge Base ──────────────────────────────────────────────────

KNOWLEDGE_BASE = [
    {
        "id": "aasm-ahi-classification",
        "source": "AASM Clinical Guidelines for Sleep Apnea Diagnosis",
        "content": (
            "The Apnea-Hypopnea Index (AHI) is the primary metric for sleep apnea severity. "
            "AHI < 5 events/hour is considered normal. "
            "AHI 5–14.9 indicates mild sleep apnea. "
            "AHI 15–29.9 indicates moderate sleep apnea. "
            "AHI ≥ 30 indicates severe sleep apnea. "
            "These thresholds are established by the American Academy of Sleep Medicine (AASM)."
        ),
        "keywords": ["ahi", "apnea-hypopnea index", "severity", "mild", "moderate", "severe", "normal ahi", "aasm"],
    },
    {
        "id": "aasm-treatment-thresholds",
        "source": "AASM Clinical Practice Guideline for CPAP Therapy",
        "content": (
            "CPAP therapy is recommended for patients with moderate to severe OSA (AHI ≥ 15). "
            "For mild OSA (AHI 5–14.9), treatment is recommended if symptoms such as excessive daytime sleepiness, "
            "cognitive impairment, or cardiovascular comorbidity are present. "
            "The standard therapeutic pressure range is 4–20 cmH2O with auto-adjusting devices."
        ),
        "keywords": ["treatment", "therapy", "cpap", "recommend", "prescribe", "threshold", "indication"],
    },
    {
        "id": "resmed-leak-rate",
        "source": "ResMed Clinical Guidelines — Mask Leak Management",
        "content": (
            "ResMed considers an unintentional leak rate below 24 L/min (95th percentile) as acceptable. "
            "Leak rates consistently above 24 L/min can compromise therapy efficacy, "
            "reduce AHI accuracy, and cause sleep disruption. "
            "Common causes: improper mask fit, incorrect mask type, high pressure settings, "
            "or mouth breathing (for nasal mask users). "
            "Solutions include mask refit, chinstrap, full-face mask, or EPR adjustment."
        ),
        "keywords": ["leak", "leak rate", "mask", "mask fit", "24 l/min", "unintentional leak", "resmed", "seal"],
    },
    {
        "id": "aasm-compliance",
        "source": "AASM & CMS Compliance Standards for CPAP Therapy",
        "content": (
            "Medicare and most insurers define CPAP compliance as device use for ≥ 4 hours per night "
            "on at least 70% of nights over a 30-day consecutive period. "
            "Patients who do not meet this threshold may lose insurance coverage for their device. "
            "The AASM recommends at least 6 hours per night for optimal therapeutic benefit. "
            "Compliance rates below 50% warrant intervention such as mask refitting, "
            "humidification adjustment, or patient re-education."
        ),
        "keywords": ["compliance", "adherence", "4 hours", "70%", "medicare", "insurance", "usage hours", "cms"],
    },
    {
        "id": "resmed-epr",
        "source": "ResMed AirSense 10/11 Clinical Guide — EPR Settings",
        "content": (
            "Expiratory Pressure Relief (EPR) reduces pressure during exhalation for patient comfort. "
            "EPR settings range from 0 (off) to 3 (maximum relief). "
            "Higher EPR can improve compliance in patients with difficulty exhaling against pressure. "
            "However, EPR may increase central apnea index (CAI) in some patients, "
            "particularly at higher levels. If treatment-emergent central sleep apnea is suspected, "
            "reducing or disabling EPR is recommended."
        ),
        "keywords": ["epr", "expiratory pressure relief", "pressure relief", "exhalation", "comfort", "central apnea"],
    },
    {
        "id": "aasm-central-apnea",
        "source": "AASM Guidelines — Central Sleep Apnea and Treatment-Emergent CSA",
        "content": (
            "Treatment-emergent central sleep apnea (TECSA, formerly 'complex sleep apnea') "
            "occurs when CPAP therapy unmasks or triggers central apneas in patients "
            "who initially had predominantly obstructive events. "
            "A central apnea index (CAI) > 5 events/hour persisting on CPAP therapy "
            "warrants clinical evaluation. Management options include: "
            "EPR reduction, transition to BiPAP with backup rate, or adaptive servo-ventilation (ASV). "
            "Central apnea has different underlying mechanisms than obstructive apnea."
        ),
        "keywords": ["central apnea", "cai", "treatment-emergent", "tecsa", "complex", "bipap", "asv"],
    },
    {
        "id": "resmed-pressure-titration",
        "source": "ResMed AutoSet Titration Protocol",
        "content": (
            "The ResMed AirSense AutoSet algorithm adjusts pressure between user-set minimum and maximum limits. "
            "Typical starting configuration: minimum 4–7 cmH2O, maximum 15–20 cmH2O. "
            "The 95th percentile pressure is a key clinical metric — it represents the pressure "
            "at or below which the patient spends 95% of the night. "
            "If the 95th percentile pressure is consistently at the maximum setting, "
            "the upper limit should be increased for optimal therapy."
        ),
        "keywords": ["pressure", "titration", "autoset", "95th", "cmh2o", "min pressure", "max pressure", "air sense"],
    },
    {
        "id": "nih-hrv-norms",
        "source": "NIH / Journal of Sleep Research — HRV in Sleep",
        "content": (
            "Heart rate variability (HRV) during sleep is a marker of autonomic nervous system function. "
            "Lower HRV during sleep is associated with poorer sleep quality, "
            "increased stress, and higher cardiovascular risk. "
            "Typical overnight HRV averages range from 25–60 ms for healthy adults, "
            "with higher values generally indicating better recovery. "
            "Consistent trends (measured over weeks) are more clinically meaningful than single-night values. "
            "HRV trends can be used as one component of sleep recovery assessment."
        ),
        "keywords": ["hrv", "heart rate variability", "autonomic", "recovery", "stress", "cardiovascular"],
    },
    {
        "id": "nih-spo2-sleep",
        "source": "NIH / American Journal of Respiratory and Critical Care Medicine — Nocturnal Oxygen",
        "content": (
            "Normal overnight SpO2 in healthy adults averages 94–98%. "
            "Sustained SpO2 below 90% during sleep is clinically significant and "
            "may indicate sleep-disordered breathing. "
            "The oxygen desaturation index (ODI) — the number of desaturations ≥ 3% per hour — "
            "is a key metric used alongside AHI for sleep apnea diagnosis. "
            "In CPAP users, residual desaturations despite adequate AHI control "
            "should prompt evaluation for other cardiopulmonary conditions."
        ),
        "keywords": ["spo2", "oxygen", "desaturation", "saturation", "odi", "90%", "nocturnal hypoxia", "blood oxygen"],
    },
    {
        "id": "aasm-sleep-stages",
        "source": "AASM Manual for the Scoring of Sleep and Associated Events",
        "content": (
            "Sleep consists of NREM (non-rapid eye movement) stages N1, N2, N3 (deep sleep) "
            "and REM sleep. In healthy adults: "
            "N1 accounts for 2–5% of total sleep time, "
            "N2 for 45–55%, "
            "N3 (deep sleep) for 15–25%, "
            "and REM for 20–25%. "
            "Low deep sleep percentage (< 15%) is associated with poorer sleep quality and recovery. "
            "Low REM percentage (< 15%) may indicate sleep disruption or depression."
        ),
        "keywords": ["sleep stage", "deep sleep", "rem", "nrem", "n3", "light sleep", "slow wave", "sleep architecture"],
    },
    {
        "id": "nih-sleep-hygiene",
        "source": "NIH / CDC — Sleep Hygiene Best Practices",
        "content": (
            "Good sleep hygiene includes maintaining a consistent sleep-wake schedule (even on weekends), "
            "keeping the bedroom dark, quiet, and cool (65–68°F / 18–20°C), "
            "avoiding screens (blue light) 60 minutes before bed, "
            "avoiding caffeine and nicotine within 6 hours of bedtime, "
            "avoiding large meals and alcohol within 3 hours of bedtime, "
            "and regular daytime exercise (but not within 2 hours of sleep). "
            "Sleep hygiene improvements are the first-line non-pharmacologic intervention for insomnia."
        ),
        "keywords": ["sleep hygiene", "bedtime routine", "caffeine", "screen time", "blue light", "exercise", "sleep schedule"],
    },
    {
        "id": "aasm-insomnia-classification",
        "source": "AASM Clinical Practice Guideline — Insomnia Management",
        "content": (
            "Insomnia is defined as difficulty initiating sleep, maintaining sleep, or early morning awakening "
            "despite adequate opportunity for sleep, occurring at least 3 nights per week for at least 3 months "
            "for chronic insomnia. Acute insomnia lasts less than 3 months. "
            "The first-line treatment is Cognitive Behavioral Therapy for Insomnia (CBT-I), "
            "which includes stimulus control, sleep restriction, cognitive restructuring, "
            "and relaxation techniques. Pharmacotherapy is generally reserved for short-term use."
        ),
        "keywords": ["insomnia", "sleep onset", "maintenance", "early awakening", "cbti", "cbt-i", "chronic insomnia", "acute insomnia"],
    },
    {
        "id": "nih-circadian-rhythm",
        "source": "NIH / National Institute of Neurological Disorders — Circadian Rhythm Disorders",
        "content": (
            "Circadian rhythm disorders occur when the internal body clock is misaligned with the external light-dark cycle. "
            "Common types: delayed sleep-wake phase disorder (night owls), advanced sleep-wake phase disorder (early birds), "
            "shift work disorder, and jet lag disorder. "
            "Treatment includes timed light exposure (bright light therapy), "
            "melatonin supplementation at appropriate times, and consistent sleep scheduling. "
            "The suprachiasmatic nucleus (SCN) in the hypothalamus is the master circadian pacemaker."
        ),
        "keywords": ["circadian rhythm", "body clock", "delayed phase", "advanced phase", "shift work", "jet lag", "light therapy", "scn"],
    },
    {
        "id": "aasm-narcolepsy",
        "source": "AASM Clinical Practice Guideline — Narcolepsy Diagnosis and Management",
        "content": (
            "Narcolepsy is a chronic neurologic disorder characterized by excessive daytime sleepiness (EDS) "
            "and cataplexy (sudden muscle weakness triggered by strong emotions) in type 1. "
            "Type 2 narcolepsy has EDS without cataplexy. "
            "Other symptoms: sleep paralysis, hypnagogic/hypnopompic hallucinations, and fragmented night sleep. "
            "Diagnosis requires a Multiple Sleep Latency Test (MSLT) showing mean sleep latency ≤ 8 minutes "
            "and 2 or more Sleep-Onset REM Periods (SOREMPs). "
            "Treatment includes scheduled naps, sodium oxybate, modafinil, and antidepressants for cataplexy."
        ),
        "keywords": ["narcolepsy", "cataplexy", "eds", "daytime sleepiness", "mslt", "sorem", "hallucinations", "sleep paralysis"],
    },
    {
        "id": "aasm-rls-diagnosis",
        "source": "AASM / International Restless Legs Syndrome Study Group — RLS Diagnostic Criteria",
        "content": (
            "Restless Legs Syndrome (RLS) is diagnosed using five essential criteria: "
            "urge to move the legs (or arms) occurring during rest or inactivity, "
            "partially or completely relieved by movement, "
            "worse in the evening or night, "
            "not solely explained by another condition, "
            "and occurring at least 3 times per week for at least 3 months for chronic RLS. "
            "Iron deficiency is a common treatable cause — ferritin levels below 75 mcg/L warrant supplementation. "
            "Treatment includes iron therapy, dopamine agonists, gabapentin, and alpha-2-delta ligands."
        ),
        "keywords": ["rls", "restless legs", "willis-ekbom", "ferritin", "iron", "dopamine", "pramipexole", "movement disorder"],
    },
    {
        "id": "aasm-pediatric-sleep-apnea",
        "source": "AASM Clinical Guideline — Pediatric OSA Diagnosis and Management",
        "content": (
            "Pediatric obstructive sleep apnea is defined as AHI ≥ 1 event/hour in children (different from adult thresholds). "
            "Common causes include adenotonsillar hypertrophy, obesity, and craniofacial abnormalities. "
            "Symptoms include snoring, mouth breathing, enuresis (bedwetting), hyperactivity, and daytime sleepiness. "
            "First-line treatment for most children is adenotonsillectomy. "
            "CPAP therapy is used when surgery is contraindicated or ineffective. "
            "Untreated pediatric OSA can lead to impaired growth, cognitive deficits, and cardiovascular complications."
        ),
        "keywords": ["pediatric", "child", "childhood", "adenotonsillectomy", "tonsil", "adenoid", "pediatric osa", "ahi 1"],
    },
    {
        "id": "aasm-bipap-indications",
        "source": "AASM Guidelines — Bi-Level Positive Airway Pressure Therapy",
        "content": (
            "BiPAP (bilevel positive airway pressure) delivers two distinct pressures: "
            "a higher inspiratory positive airway pressure (IPAP) and a lower expiratory positive airway pressure (EPAP). "
            "It is indicated for patients who cannot tolerate CPAP, require high pressure support, "
            "have obesity hypoventilation syndrome (OHS), neuromuscular disease affecting breathing, "
            "or treatment-emergent central sleep apnea. "
            "The difference between IPAP and EPAP (pressure support) aids ventilation and carbon dioxide clearance. "
            "BiPAP with backup rate (ST mode) is used for central sleep apnea and hypoventilation disorders."
        ),
        "keywords": ["bipap", "bilevel", "ipap", "epap", "pressure support", "ventilation", "ohs", "neuromuscular", "hypoventilation"],
    },
    {
        "id": "nih-nocturnal-oxygen",
        "source": "NIH / ATS Clinical Practice Guideline — Home Oxygen Therapy",
        "content": (
            "Nocturnal oxygen therapy is prescribed when overnight SpO2 falls below 88% for at least 5 minutes. "
            "Oxygen can be delivered via nasal cannula at 1–4 L/min during sleep. "
            "For patients with COPD and nocturnal desaturation, long-term oxygen therapy (> 15 hours/day, including sleep) "
            "improves survival. In OSA patients using CPAP, residual desaturation despite adequate AHI control "
            "should prompt evaluation for underlying cardiopulmonary disease rather than automatic oxygen supplementation."
        ),
        "keywords": ["oxygen", "nocturnal oxygen", "supplemental oxygen", "o2", "desaturation", "copd", "nasal cannula", "hypoxia"],
    },
    {
        "id": "resmed-positional-therapy",
        "source": "ResMed Clinical Guidance — Positional Obstructive Sleep Apnea",
        "content": (
            "Positional OSA is defined as an AHI at least twice as high in the supine (back) position "
            "compared to the non-supine (side) position. Approximately 50–60% of OSA patients have positional disease. "
            "Positional therapy includes the use of specialized pillows, wearable vibration devices, "
            "or the 'tennis ball technique' to discourage supine sleeping. "
            "Positional therapy alone is effective for selected patients with mild-to-moderate positional OSA. "
            "It can also be used as an adjunct to CPAP therapy to reduce pressure requirements."
        ),
        "keywords": ["positional", "supine", "side sleeping", "back sleep", "tennis ball", "positional therapy", "positional osa"],
    },
    {
        "id": "nih-weight-loss-osa",
        "source": "NIH / Sleep Medicine Reviews — Weight Loss and Obstructive Sleep Apnea",
        "content": (
            "Weight loss is a highly effective treatment for OSA in overweight and obese patients. "
            "A 10% reduction in body weight is associated with a 26–32% reduction in AHI. "
            "Bariatric surgery can lead to OSA remission in 40–60% of patients. "
            "Weight loss reduces pharyngeal fat pad volume, improving upper airway patency. "
            "Combining CPAP with weight loss is more effective than either alone. "
            "However, OSA may persist even after significant weight loss, requiring continued therapy monitoring."
        ),
        "keywords": ["weight loss", "bariatric", "obesity", "bmi", "overweight", "weight reduction", "pharyngeal fat", "diet"],
    },
    {
        "id": "resmed-cpap-cleaning",
        "source": "ResMed / FDA — CPAP Equipment Cleaning and Maintenance Guidelines",
        "content": (
            "CPAP equipment should be cleaned regularly to prevent respiratory infections and maintain device function. "
            "Mask cushion and water chamber: daily wash with mild soap and warm water. "
            "Mask frame and headgear: weekly wash. "
            "Tubing: weekly wash and hung to dry completely. "
            "Filters: replace disposable filters monthly, wash reusable filters every 2 weeks. "
            "Ozone and UV cleaners are not FDA-approved and may damage equipment. "
            "CPAP supplies (mask, tubing, water chamber) should be replaced every 3–6 months."
        ),
        "keywords": ["clean", "cleaning", "maintenance", "mask care", "tubing", "filter", "hygiene", "ozone", "fda"],
    },
    {
        "id": "resmed-travel-cpap",
        "source": "ResMed — Travel CPAP Guide and FAA Compliance",
        "content": (
            "CPAP devices are FAA-approved for use during air travel as medical devices — "
            "they are exempt from the ban on portable electronic devices during takeoff and landing. "
            "Travel-sized CPAP machines (e.g., ResMed AirMini, Philips DreamStation Go) weigh under 1 lb. "
            "CPAP users should use distilled water in hotel rooms to prevent mineral buildup. "
            "Many travel CPAPs use humidification cartridges instead of built-in water chambers. "
            "Most airlines allow CPAP as a carry-on medical device without counting toward baggage limits — "
            "a doctor's note is recommended but not always required."
        ),
        "keywords": ["travel", "airplane", "flight", "faa", "airmini", "portable", "carry-on", "vacation", "hotel"],
    },
    {
        "id": "resmed-humidification",
        "source": "ResMed Clinical Guide — Heated Humidification in CPAP Therapy",
        "content": (
            "Heated humidification in CPAP therapy improves comfort and compliance by reducing nasal dryness, "
            "nasal congestion, and throat irritation. "
            "Optimal humidity settings depend on ambient conditions: higher humidity in dry/cold climates, "
            "lower humidity in warm/humid climates to prevent rainout (water condensation in the tubing). "
            "Heated tubing (ClimateLineAir) prevents rainout by maintaining a constant temperature along the tube. "
            "The ResMed AirSense 10/11 Auto Set feature allows automatic humidity control based on ambient conditions. "
            "Inadequate humidification is a common reason for CPAP discontinuation."
        ),
        "keywords": ["humidifier", "humidity", "rainout", "dry mouth", "nasal dryness", "heated tubing", "climate control", "comfort"],
    },
    {
        "id": "resmed-pressure-optimization",
        "source": "ResMed AutoSet Algorithm — Pressure Optimization Protocol",
        "content": (
            "Optimal CPAP pressure is the minimum pressure that prevents 95% of obstructive events. "
            "For auto-adjusting CPAP devices, the 95th percentile pressure over 30 days is used to determine "
            "a fixed pressure if switching to CPAP mode. "
            "Pressure requirements change over time with weight loss/gain, positional changes, "
            "or upper airway surgery. "
            "If AHI remains elevated despite adequate pressure, check for large mask leak, "
            "central apnea emergence, or pressure insufficient for REM-stage specific events. "
            "Residual AHI < 5 events/hour is generally considered controlled."
        ),
        "keywords": ["pressure", "optimal pressure", "95th percentile", "fixed pressure", "autoset", "pressure adjustment", "rem pressure"],
    },
    {
        "id": "resmed-ramp-feature",
        "source": "ResMed AirSense Clinical Manual — Ramp Feature",
        "content": (
            "The ramp feature gradually increases CPAP pressure from a low start pressure "
            "to the prescribed therapeutic pressure over a set duration (5–45 minutes). "
            "Ramp improves comfort during sleep onset by preventing sensation of full pressure while awake. "
            "For ResMed devices, the ramp start pressure can be set from 4 cmH2O (default). "
            "Some patients may experience events during ramp if their starting pressure is too low. "
            "Auto-ramp detects sleep onset (via breathing pattern analysis) and delays start accordingly. "
            "Newer devices automatically transition from ramp to therapy without fixed timer."
        ),
        "keywords": ["ramp", "start pressure", "ramp time", "auto ramp", "comfort", "sleep onset", "pressure start"],
    },
    {
        "id": "aasm-sleep-study-types",
        "source": "AASM Clinical Guidelines — Types of Sleep Studies",
        "content": (
            "Type 1 (in-laboratory PSG) — overnight attended polysomnography with EEG, EOG, EMG, "
            "ECG, airflow, respiratory effort, snore microphone, and oximetry. Gold standard for sleep apnea diagnosis. "
            "Type 2 — comprehensive portable device with ≥ 7 channels, unattended. "
            "Type 3 (home sleep test / HST) — limited portable device with 4–7 channels "
            "(typically airflow, respiratory effort, oximetry, pulse). Used for uncomplicated OSA diagnosis. "
            "Type 4 — single or dual-channel screening devices (usually oximetry only). "
            "Home sleep tests cannot diagnose central sleep apnea or other non-OSA sleep disorders."
        ),
        "keywords": ["sleep study", "polysomnography", "psg", "home sleep test", "hst", "type 3", "portable", "diagnosis", "attended"],
    },
    {
        "id": "nih-epworth-sleepiness-scale",
        "source": "NIH — Epworth Sleepiness Scale (ESS) — Standard Reference",
        "content": (
            "The Epworth Sleepiness Scale (ESS) is an 8-question self-assessment measuring daytime sleepiness. "
            "Each item is scored 0–3 (0 = would never doze, 3 = high chance of dozing) across common daily scenarios. "
            "Total scores: 0–5 (normal daytime sleepiness), 6–10 (mild excessive), "
            "11–15 (moderate excessive), and 16–24 (severe excessive daytime sleepiness). "
            "ESS > 10 is considered clinically significant and warrants further sleep evaluation. "
            "The ESS is used to assess symptom severity and response to OSA treatment."
        ),
        "keywords": ["epworth", "ess", "sleepiness scale", "daytime sleepiness", "doze", "self-assessment", "questionnaire"],
    },
    {
        "id": "aasm-snoring-assessment",
        "source": "AASM Clinical Consensus — Snoring Assessment and Treatment",
        "content": (
            "Snoring is caused by vibration of pharyngeal soft tissues due to partial upper airway obstruction. "
            "It affects approximately 40% of men and 24% of women. "
            "Snoring alone (without apnea/hypopnea) is termed primary snoring — it does not cause significant "
            "oxygen desaturation or sleep fragmentation. However, it may indicate elevated risk for developing OSA. "
            "Treatment options for primary snoring include weight loss, positional therapy, "
            "oral appliances (mandibular advancement devices), nasal dilator strips, "
            "and surgery (uvulopalatopharyngoplasty / UPPP) for severe cases."
        ),
        "keywords": ["snore", "snoring", "primary snoring", "uppp", "oral appliance", "mandibular advancement", "nasal strip"],
    },
    {
        "id": "nih-sleep-mental-health",
        "source": "NIH / Journal of Clinical Sleep Medicine — Sleep and Mental Health",
        "content": (
            "There is a bidirectional relationship between sleep disorders and mental health conditions. "
            "Chronic insomnia increases the risk of developing depression by 2–3 times. "
            "OSA is associated with higher rates of depression, anxiety, and cognitive impairment. "
            "CPAP therapy has been shown to improve depressive symptoms and quality of life in OSA patients. "
            "Sleep deprivation impairs emotional regulation, increases irritability, "
            "and reduces the effectiveness of psychiatric treatments. "
            "Treating underlying sleep disorders is an essential component of mental health management."
        ),
        "keywords": ["mental health", "depression", "anxiety", "bipolar", "cognitive", "emotional regulation", "psychiatry", "mood"],
    },
    {
        "id": "nih-sleep-cardiovascular",
        "source": "NIH / American Heart Association — Sleep and Cardiovascular Health",
        "content": (
            "Untreated OSA is an independent risk factor for hypertension, coronary artery disease, "
            "heart failure, atrial fibrillation, and stroke. "
            "The severity of hypoxia during sleep correlates with cardiovascular risk more strongly than AHI alone. "
            "CPAP therapy reduces blood pressure by 2–5 mmHg on average (greater effect in patients with resistant hypertension). "
            "Sleep duration < 6 hours per night is associated with a 20–30% increased risk of cardiovascular events. "
            "Irregular sleep schedules and shift work are also linked to higher cardiovascular morbidity."
        ),
        "keywords": ["cardiovascular", "heart", "hypertension", "blood pressure", "afib", "atrial fibrillation", "stroke", "heart disease"],
    },
    {
        "id": "nih-sleep-metabolic",
        "source": "NIH — Sleep and Metabolic Health / Diabetes Review",
        "content": (
            "Short sleep duration (< 6 hours) and poor sleep quality are associated with increased risk of type 2 diabetes, "
            "insulin resistance, and obesity. "
            "OSA itself contributes to glucose intolerance independent of obesity. "
            "CPAP therapy improves insulin sensitivity in patients with OSA and prediabetes. "
            "Sleep deprivation alters levels of leptin (satiety hormone, decreased) "
            "and ghrelin (hunger hormone, increased), leading to increased appetite and cravings. "
            "Sleep optimization is now recommended as part of comprehensive metabolic disease management."
        ),
        "keywords": ["diabetes", "metabolic", "insulin", "glucose", "obesity", "leptin", "ghrelin", "prediabetes", "weight"],
    },
    {
        "id": "nih-sleep-cognition",
        "source": "NIH / Nature Reviews Neuroscience — Sleep and Cognitive Function",
        "content": (
            "Sleep is essential for memory consolidation, particularly declarative (fact-based) "
            "and procedural (skill-based) memory. "
            "N3 (deep sleep) is critical for memory consolidation, while REM sleep supports emotional memory processing. "
            "Chronic sleep deprivation impairs attention, working memory, decision-making, and reaction time. "
            "OSA patients show measurable cognitive deficits that partially reverse with CPAP therapy. "
            "The hippocampus, critical for memory formation, is particularly vulnerable to sleep-disordered breathing. "
            "Cognitive improvement from CPAP therapy typically becomes apparent after 3–6 months of consistent use."
        ),
        "keywords": ["cognition", "memory", "brain", "hippocampus", "attention", "focus", "cognitive decline", "consolidation"],
    },
    {
        "id": "nih-melatonin",
        "source": "NIH / National Center for Complementary and Integrative Health — Melatonin",
        "content": (
            "Melatonin is a naturally occurring hormone produced by the pineal gland in response to darkness. "
            "It regulates the circadian rhythm and sleep-wake cycle. "
            "Supplemental melatonin (0.5–5 mg, taken 1–2 hours before bed) is effective for: "
            "circadian rhythm disorders (delayed sleep phase, jet lag, shift work), "
            "and certain sleep disorders in children with neurodevelopmental conditions. "
            "Melatonin is not generally recommended for chronic insomnia in adults — CBT-I is more effective. "
            "Extended-release formulations provide sustained levels through the night. "
            "Side effects are mild but may include headache, dizziness, and next-day drowsiness."
        ),
        "keywords": ["melatonin", "supplement", "pineal", "circadian", "jet lag", "sleep aid", "natural", "dosage"],
    },
    {
        "id": "aasm-cbti-protocol",
        "source": "AASM Clinical Practice Guideline — Cognitive Behavioral Therapy for Insomnia (CBT-I)",
        "content": (
            "CBT-I is the first-line treatment for chronic insomnia, recommended by the AASM, "
            "American College of Physicians, and European Sleep Research Society. "
            "Components include: stimulus control (only go to bed when sleepy, get out of bed if not sleeping), "
            "sleep restriction therapy (limit time in bed to actual sleep time), "
            "cognitive restructuring (address dysfunctional beliefs about sleep), "
            "relaxation training (progressive muscle relaxation, guided imagery, diaphragmatic breathing), "
            "and sleep hygiene education. Typical treatment is 4–8 weekly sessions. "
            "Effectiveness is comparable or superior to sleep medications with no side effects."
        ),
        "keywords": ["cbti", "cbt-i", "cognitive behavioral", "stimulus control", "sleep restriction", "therapy", "insomnia treatment"],
    },
    {
        "id": "resmed-mask-types",
        "source": "ResMed Mask Selection Guide — Clinical Recommendations",
        "content": (
            "CPAP masks fall into three main categories: "
            "Nasal masks (e.g., ResMed AirFit N30i) — cover only the nose, suitable for patients who breathe through their nose. "
            "Nasal pillow masks (e.g., ResMed AirFit P30i) — insert directly into nostrils, minimal contact, "
            "ideal for claustrophobic patients or those with facial hair. "
            "Full-face masks (e.g., ResMed AirFit F30i/F40) — cover nose and mouth, "
            "required for mouth breathers or patients requiring higher pressures. "
            "Proper mask fit is the strongest predictor of CPAP adherence. "
            "Patients should be offered a choice of mask types to improve compliance."
        ),
        "keywords": ["mask", "mask type", "nasal", "full face", "nasal pillow", "fit", "selection", "adherence", "f30i", "p30i"],
    },
    {
        "id": "nih-wearable-accuracy",
        "source": "NIH / JAMA Internal Medicine — Consumer Wearable Sleep Tracking Accuracy",
        "content": (
            "Consumer wearables (Fitbit, Apple Watch, Garmin, Whoop) estimate sleep stages using "
            "actigraphy (movement) and heart rate data. They are reasonably accurate for sleep vs wake detection "
            "but significantly less accurate for sleep stage classification compared to PSG (EEG). "
            "Wearables tend to overestimate total sleep time and underestimate wake after sleep onset (WASO). "
            "They cannot reliably diagnose sleep apnea — home sleep tests (Type 3 devices) remain the minimum standard. "
            "Despite limitations, wearables are useful for tracking long-term sleep trends and sleep hygiene improvements."
        ),
        "keywords": ["wearable", "fitbit", "apple watch", "actigraphy", "garmin", "whoop", "tracker", "consumer device", "accuracy"],
    },
    {
        "id": "aasm-ahi-vs-rdi",
        "source": "AASM Scoring Manual — AHI, RDI, and RERA Definitions",
        "content": (
            "AHI (Apnea-Hypopnea Index) counts apneas (complete cessation of airflow ≥ 10s) "
            "and hypopneas (reduced airflow ≥ 10s with ≥ 3% desaturation or arousal) per hour of sleep. "
            "RDI (Respiratory Disturbance Index) includes all AHI events plus RERAs "
            "(Respiratory Effort-Related Arousals — breathing-related arousals not meeting apnea/hypopnea criteria). "
            "RDI is always ≥ AHI. Some patients with low AHI but high RDI (UARS) may have significant symptoms. "
            "Home sleep tests (Type 3) typically report AHI or pAHI (pseudo-AHI) — they cannot detect RERAs. "
            "In-lab PSG is required to measure full RDI."
        ),
        "keywords": ["ahi", "rdi", "rera", "apnea-hypopnea", "respiratory disturbance", "arousal", "scoring", "diagnosis"],
    },
    {
        "id": "aasm-uars",
        "source": "AASM Consensus Statement — Upper Airway Resistance Syndrome (UARS)",
        "content": (
            "Upper Airway Resistance Syndrome (UARS) is characterized by increased respiratory effort "
            "leading to frequent arousals without meeting standard apnea or hypopnea criteria. "
            "Patients with UARS typically have AHI < 5 but RDI > 10. "
            "Symptoms include excessive daytime sleepiness, fatigue, insomnia, morning headaches, "
            "and difficulty concentrating — similar to mild OSA. "
            "UARS patients are often younger, non-obese, and female. "
            "Diagnosis requires in-lab PSG with esophageal manometry or diaphragmatic EMG. "
            "Treatment includes CPAP, oral appliances, or nasal surgery."
        ),
        "keywords": ["uars", "upper airway resistance", "rera", "flow limitation", "nasal resistance", "effort", "arousal without apnea"],
    },
    {
        "id": "aasm-cheyne-stokes",
        "source": "AASM International Classification of Sleep Disorders — Cheyne-Stokes Respiration",
        "content": (
            "Cheyne-Stokes respiration (CSR) is a pattern of cyclic crescendo-decrescendo breathing "
            "alternating with central apneas or hypopneas, commonly seen in patients with heart failure "
            "or neurologic conditions. CSR is defined as ≥ 3 consecutive cycles of waxing-waning breathing "
            "with a cycle length of at least 60 seconds. "
            "CSR is present in 30–50% of patients with heart failure with reduced ejection fraction (HFrEF). "
            "Unlike OSA, CSR is a central (neurological) breathing pattern rather than an obstructive airway issue. "
            "Adaptive servo-ventilation (ASV) is the primary treatment for CSR-related sleep-disordered breathing."
        ),
        "keywords": ["cheyne-stokes", "csr", "heart failure", "central apnea", "waxing waning", "asv", "hfrref", "cardiac"],
    },
    {
        "id": "resmed-cpap-side-effects",
        "source": "ResMed Clinical Support — Managing CPAP Side Effects",
        "content": (
            "Common CPAP side effects and solutions: "
            "Aerophagia (swallowing air): reduce pressure, enable EPR, avoid sleeping supine. "
            "Dry mouth: use a full-face mask (if nasal mask) or chinstrap, increase humidity. "
            "Nasal congestion: enable heated humidification, use saline spray, check for allergies. "
            "Claustrophobia: try nasal pillow mask (minimal face contact), use ramp, gradual desensitization. "
            "Skin irritation or pressure sores: check mask fit (may need different size), use mask liner. "
            "Machine noise: check filter for blockage, place device below head level. "
            "Device intolerance: low pressure avoidance, retry 30–60 min before sleep for adaption."
        ),
        "keywords": ["side effects", "aerophagia", "dry mouth", "claustrophobia", "mask leak", "skin irritation", "nasal congestion", "discomfort"],
    },
    {
        "id": "nih-shift-work-sleep",
        "source": "NIH / National Institute for Occupational Safety and Health — Shift Work and Sleep",
        "content": (
            "Shift work disorder affects approximately 15–20% of night shift workers. "
            "Symptoms include excessive sleepiness during work hours and insomnia during scheduled sleep times. "
            "Strategic countermeasures: take a 20–30 min nap before shift, "
            "expose to bright light during the first half of the shift, wear blue-blocking glasses "
            "during the commute home, sleep in a completely dark and quiet room, "
            "maintain a consistent sleep schedule even on days off as much as possible, "
            "and use melatonin (0.5–3 mg) before daytime sleep. "
            "Caffeine should be avoided during the last half of the shift to not interfere with post-shift sleep."
        ),
        "keywords": ["shift work", "night shift", "rotating shift", "niosh", "circadian misalignment", "graveyard", "sleep schedule"],
    },
    {
        "id": "aasm-children-sleep-requirements",
        "source": "AASM Consensus Statement — Recommended Sleep Durations for Children",
        "content": (
            "The AASM recommends the following sleep durations per 24 hours (including naps): "
            "Infants 4–12 months: 12–16 hours. "
            "Children 1–2 years: 11–14 hours. "
            "Children 3–5 years: 10–13 hours. "
            "Children 6–12 years: 9–12 hours. "
            "Teenagers 13–18 years: 8–10 hours. "
            "Insufficient sleep in children is associated with obesity, impaired academic performance, "
            "behavioral problems (including ADHD-like symptoms), and increased injury risk. "
            "Screen time before bed is particularly disruptive to children's sleep due to blue light sensitivity."
        ),
        "keywords": ["children", "sleep duration", "recommended hours", "infant", "toddler", "teen", "pediatric sleep", "screen time"],
    },
    {
        "id": "nih-elderly-sleep",
        "source": "NIH / National Institute on Aging — Sleep Changes in Older Adults",
        "content": (
            "Normal aging is associated with several sleep changes: "
            "lighter sleep (more time in N1 and N2, less N3 deep sleep), "
            "more frequent nighttime awakenings, earlier bedtime and wake times (advanced phase), "
            "more time spent in bed but less total sleep time. "
            "Total sleep need remains about 7–9 hours despite increased fragmentation. "
            "Older adults are more prone to sleep disorders: insomnia (40% of over-65s), "
            "sleep apnea (higher prevalence), RLS, and REM sleep behavior disorder. "
            "Sleep medications should be used with extreme caution due to fall risk and cognitive side effects. "
            "Bright light exposure during daytime and consistent sleep schedules are particularly helpful."
        ),
        "keywords": ["elderly", "older adults", "aging", "sleep changes", "seniors", "lighter sleep", "advanced phase", "fall risk"],
    },
    {
        "id": "nih-sleep-immune",
        "source": "NIH / Journal of Experimental Medicine — Sleep and Immune Function",
        "content": (
            "Sleep is a critical modulator of immune function. During sleep, the body increases production "
            "of cytokines (IL-6, TNF-alpha) and infection-fighting T-cells. "
            "Chronic sleep deprivation (< 6 hours per night) is associated with a 3–4 times higher risk "
            "of developing a common cold after viral exposure. "
            "Sleep also enhances the effectiveness of vaccination — well-rested individuals mount stronger antibody responses. "
            "Sleep disruption increases systemic inflammation markers (CRP, IL-6, TNF-alpha). "
            "Improving sleep quality is recommended as part of a comprehensive approach to immune health."
        ),
        "keywords": ["immune", "immunity", "infection", "cold", "vaccine", "antibody", "inflammation", "cytokine", "t-cell"],
    },
    {
        "id": "aasm-surgery-risk-osa",
        "source": "AASM Clinical Consensus — Perioperative Management of OSA Patients",
        "content": (
            "OSA patients have significantly higher risk of perioperative complications including "
            "difficult intubation, postoperative oxygen desaturation, cardiac events, "
            "and prolonged hospital stay. "
            "All patients should be screened for OSA before elective surgery (STOP-Bang questionnaire). "
            "Confirmed OSA patients should bring their CPAP device for hospitalization, "
            "use it during all sleep periods post-surgery, and be monitored with continuous pulse oximetry. "
            "Opioid use should be minimized due to respiratory-depressant effects compounding OSA risk. "
            "High-risk patients may require ICU-level care for the first 24 hours post-operatively."
        ),
        "keywords": ["surgery", "anesthesia", "perioperative", "stop-bang", "cpap during surgery", "complication", "opioid", "icu"],
    },
]


def search_knowledge(query: str, top_k: int = 3) -> list:
    """
    Search the embedded medical knowledge base for relevant entries.

    Args:
        query: Natural language question or keywords
        top_k: Maximum number of results to return

    Returns:
        List of {'source': str, 'content': str, 'relevance': float} dicts
    """
    query_lower = query.lower()
    query_words = set(re.findall(r'[a-z0-9]+', query_lower))

    scored = []
    for entry in KNOWLEDGE_BASE:
        keywords_lower = [k.lower() for k in entry['keywords']]
        score = 0
        for kw in keywords_lower:
            if kw in query_lower:
                score += 2
            for qw in query_words:
                if len(qw) > 3 and qw in kw:
                    score += 1
        if score > 0:
            scored.append({
                'source': entry['source'],
                'content': entry['content'],
                'relevance': round(score, 1),
            })

    scored.sort(key=lambda x: x['relevance'], reverse=True)
    return scored[:top_k]


def build_knowledge_context(query: str) -> str:
    """
    Build a grounded knowledge context string for injection into the system prompt.

    Args:
        query: The user's question or context

    Returns:
        Formatted string with cited knowledge snippets
    """
    results = _try_azure_search(query) if os.getenv('FOUNDRY_IQ_ENDPOINT') else search_knowledge(query)
    if not results:
        return ''

    lines = ['\n--- Grounded Medical Knowledge ---']
    for i, r in enumerate(results, 1):
        lines.append(f'[{i}] Source: {r["source"]}')
        lines.append(f'    {r["content"]}')
    lines.append('---\n')
    return '\n'.join(lines)


def _try_azure_search(query: str) -> list:
    """Attempt Azure AI Search lookup; return empty list on failure."""
    try:
        from azure.core.credentials import AzureKeyCredential
        from azure.search.documents import SearchClient

        endpoint = os.getenv('FOUNDRY_IQ_ENDPOINT')
        index    = os.getenv('FOUNDRY_IQ_INDEX_NAME', 'sleep-medical-knowledge')
        key      = os.getenv('FOUNDRY_IQ_API_KEY')

        if not endpoint or not key:
            return []

        client = SearchClient(endpoint=endpoint, index_name=index,
                              credential=AzureKeyCredential(key))
        results = client.search(query, top=3, select=['source', 'content'])
        return [{'source': r['source'], 'content': r['content'], 'relevance': r['@search.score']}
                for r in results]

    except Exception as e:
        print(f'[Sleep IQ] Foundry IQ search failed ({e}), using embedded KB.')
        return search_knowledge(query)


if __name__ == '__main__':
    for q in ['average ahi is 25', 'high leak rate at night', 'low hrv during sleep']:
        print(f'\nQuery: {q}')
        ctx = build_knowledge_context(q)
        print(ctx if ctx else '(no results)')
