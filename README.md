# OppFinder

Helps university undergraduate, graduate and post graduate in Nigeria find scholarships, internships, jobs and learning
opportunities they may qualify for, and explains in plain English why, what to prepare,
and the deadline. Built for OPEN//BUILD 2026 (OSCA Ile-Ife, Hacktoberfest 2026).

> **Status:** early prototype. Opportunity data is collected by hand from official pages.
> Always confirm details on the official link shown with each result.

## 1. The problem
University students often discover scholarships, internships, jobs and learning opportunities through scattered channels such as WhatsApp groups, social media, friends and websites. Finding opportunities is only part of the challenge: students also need to determine whether they qualify, understand the requirements and keep track of deadlines.

To understand these challenges, we asked **28 students** about their opportunity-search experiences. Among the respondents:

- **24** had searched for an opportunity they ultimately did not apply for.
- **25** had found an opportunity and later discovered they were ineligible at least once.
- Finding opportunities and determining eligibility were the most frequently reported frustrations.
- **27** said they would definitely or probably use a tool that recommends relevant opportunities and explains eligibility.

OppFinder addresses these challenges by bringing opportunity records together, filtering and ranking them against student profiles, and using an open-weight language model to explain potential matches in plain English. When a student does not qualify yet, it also shows what is missing and suggests what to do next.

## 2. How it works
1. A student enters course, level, interests and what they want.
2. Plain-code **rules** remove anything expired or not open to them and rank the rest.
3. The **open-weight model** writes a short "why you may fit / what to prepare / next step".
4. A separate team feature lets us paste a messy announcement and the model drafts a
   structured record, which a human checks before saving.
5. If a student doesn’t qualify yet, the app doesn’t hide the opportunity. When exactly one rule fails (their level or course), it shows what is missing and suggests next steps, such as checking the official page for the next intake or looking for similar opportunities.

## 3. The model 
- **Model:** SmolLM2-360M-Instruct by Hugging Face (HuggingFaceTB), about 360 million parameters. We run it locally through Ollama as `smollm2:360m` (725 MB download). Source: https://huggingface.co/HuggingFaceTB/SmolLM2-360M-Instruct
- **Licence:** Apache 2.0, checked on 2026-10-27 at the model card above (https://huggingface.co/HuggingFaceTB/SmolLM2-360M-Instruct/blob/main/README.md). Open weights are not automatically open source, so we read the licence terms before using the model.
- **Role:** reads a pasted opportunity announcement and drafts a structured record (a person checks it before saving), and writes a short plain-English explanation of why a student may qualify. It is not used for matching decisions: plain-code rules decide who qualifies.
- **Why this model:** it is small enough to run on student laptops with limited memory. We first tried Qwen2.5-1.5B, but it took a while to respond on our laptop and caused the computer to stop responding, so we switched to a smaller model.
- **Known limitations:**
  - The model card says it mainly handles English and may not be factually accurate, so every result links to the official page for confirmation.
  - May misread dates or eligibility rules when drafting records, so drafts are checked by a person.

## 4. Run it
```bash
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
Settings are optional environment variables, see .env.example for the names.                              

# the model (needs https://ollama.com installed)
ollama pull smollm2:360m       

uvicorn backend.main:app --reload     # API + test page at http://localhost:8000/docs
python app.py                         # student screen (second terminal)
```
Run tests: `pytest`

# Optional: temporary public demo link

The judges can run OppFinder with the steps above. As a convenience, the screen can also be shared through a temporary public link made by Gradio. **This link is not permanent hosting.** The app still runs on one of our laptops, so the link only works while that laptop is on, online, and running the API and Ollama. It also expires after about a week.

**Current demo link: https://4e1a18179c6693f112.gradio.live created at 00:20 on 29-10-26

If the link does not open, please use the demo video or the run instructions above.

### How we create the link
1. Start Ollama and the API (see "Run it").
2. In a second terminal, from the project folder, switch on the virtual environment and run:

```powershell
$env:SHARE="1"
python app.py
```

3. Gradio prints a public address ending in `.gradio.live`. Copy it.

Without `SHARE=1`, the app is only available on your own computer at `http://127.0.0.1:7860`, so no public link is created by accident.

### What to know before using it
- The first reply from the model can take a minute or more on our laptop CPU.
- The public screen only searches the opportunity list and drafts records. It does not save or change any data.
- Please do not enter personal or private information.
- Results are from a small, hand-collected dataset, so always confirm details on the official page.

## 5. Project layout
```
backend/models.py    the two "forms": Opportunity (record) and StudentProfile
backend/store.py     reads/writes data/opportunities.json
backend/matcher.py   rule-based matching and ranking (no AI)
backend/llm.py       everything that talks to the model
backend/main.py      the API endpoints
app.py               simple Gradio screen
data/                the opportunity records (real ones need a link + date_collected)
tests/               tests for matching and model-output parsing
```

## 6. Data rules
- Every record needs the **official link** and the date a human last checked it.
- Records with `"is_example": true` are placeholders and never shown to students by default.
- No scraping; no private or personal data in this repo; no API keys (use `.env`, which is git-ignored).

## 7. Technical decisions

- **Rules decide who qualifies; the model only explains and drafts.** Whether a student qualifies (level, course, type, deadline) is decided by plain code in `backend/matcher.py`, because rules are fast, predictable and can be tested. The model never makes that decision, so it can't invent an eligibility rule.
- **A small open-weight model run locally.** We use SmolLM2-360M-Instruct (Apache 2.0) through Ollama, because it can run on student laptops with limited memory and needs no paid service or API keys. We first tried Qwen2.5-1.5B, but it was too slow on our hardware. The trade-off is lower answer quality, which we describe in section 9.
- **Two jobs for the model.** It writes short plain-English explanations for matches, and it explains what is missing for opportunities a student does not qualify for yet. It can also draft a structured record from a pasted announcement.
- **"Not eligible yet" instead of hiding opportunities.** If exactly one rule fails (level or course), the app shows the opportunity with the gap in plain words and a next step. The gap comes from the rules. Only the advice comes from the model.
- **Model output is checked.** Drafted records are validated with Pydantic. The code cleans up common small-model mistakes, such as writing "None" instead of leaving a field empty, and every draft must be reviewed by a person against the official page before it is saved.
- **Real data only.** Opportunities are collected by hand from official pages. Each record needs an official link and the date it was checked. We do not scrape websites. Placeholder records are marked `is_example` and are hidden from students.
- **It still works if the model is slow or down.** If the model does not answer, the app shows the rule-based reasons and next steps instead, so results are never blank.
- **Kept fast on a CPU.** Only the top 3 matches and 2 "not yet" items get a model explanation, replies are capped in length, and the timeout can be changed with `LLM_TIMEOUT`.
- **Simple structure.** FastAPI serves the logic, and a small Gradio screen sits on top, so the API can be used on its own. Data is stored in a JSON file for simplicity. A database such as SQLite is a next step.


## 8. Acknowledgements and AI-assisted work 
- Libraries: FastAPI, Pydantic, Gradio, Requests, Ollama.
- AI-assisted work: the initial project scaffold was drafted with an AI assistant (Claude) and
  reviewed by the team.

## 9. Data sources
Opportunity records are collected by hand from official pages and stored in `data/opportunities.json`. Each record has the official link and the date it was last checked. We do not scrape websites, and details can change, so students should always confirm on the official page.

Sources used (checked October 2026):
- - [MTN Science and Technology Scholarship (STS)](https://www.mtn.ng/scholarships/) (MTN Foundation), checked 2026-10-25
- [MTN Scholarship for Blind Students (SBS)](https://www.mtn.ng/scholarships/) (MTN Foundation), checked 2026-10-25
- [MTN Top 10 UTME Scholarship](https://www.mtn.ng/scholarships/) (MTN Foundation), checked 2026-10-25
- [MTN FoundationûMUSON Music Scholarship](https://www.mtn.ng/muson/) (MTN Foundation & MUSON), checked 2026-10-01
- [NLNG Undergraduate Scholarship Scheme](https://jobs.dragnet-solutions.com/nlngscholarship/home) (Nigeria LNG Limited (NLNG)), checked 2026-10-25
- [Mastercard Foundation Scholars Program at UCT](https://uct.ac.za/mastercardfdn/apply-mastercard-foundation-scholars-program) (Mastercard Foundation & University of Cape Town), checked 2026-10-25
- [Mastercard Foundation Scholars Program at KNUST](https://apps.knust.edu.gh/nkabomapply) (Mastercard Foundation & KNUST), checked 2026-10-01
- [Chevening Scholarships (Nigeria) 2027/28](https://www.chevening.org/scholarship/nigeria/) (UK FCDO), checked 2026-10-25
- [Cowrywise Ambassadors Scholarship Program](https://ambassadors.cowrywise.com/scholarship) (Cowrywise & CFA Institute), checked 2026-10-01
- [AIMS South Africa û Google DeepMind AI for Science Master's Scholarship](https://ai.aims.ac.za/) (Google DeepMind & AIMS), checked 2026-10-25
- [DAAD In-Country / In-Region Scholarships](https://cooperation.ucad.sn/sites/default/files/ICIR_Fact%20Sheet_2027_1_compressed.pdf) (DAAD (Germany)), checked 2026-10-25
- [Seplat Energy Undergraduate Scholarship](https://seplatenergy.com/sustainability/csr/) (Seplat Energy Plc), checked 2026-10-01
- [Shell Nigeria University Scholarship](https://www.shell.com.ng/sustainability/communities/scholarships.html) (SPDC / Shell Nigeria), checked 2026-10-01
- [Federal Government BEA Overseas Scholarship](https://education.gov.ng/) (Federal Ministry of Education (Nigeria)), checked 2026-10-01
- [NDDC Local Postgraduate Scholarship](https://www.nddc.gov.ng/) (Niger Delta Development Commission), checked 2026-10-01
- [Gates Cambridge Scholarship 2027/28](https://www.gatescambridge.org/apply/timeline/) (Gates Cambridge Trust), checked 2026-10-25
- [Commonwealth Master's and PhD Scholarships 2027/28](https://cscuk.fcdo.gov.uk/) (Commonwealth Scholarship Commission (UK)), checked 2026-10-25
- [PTDF Overseas Postgraduate Scholarship 2026/27](https://scholarship.ptdf.gov.ng/guidelines) (Petroleum Technology Development Fund (Nigeria)), checked 2026-10-25
- [PTDF In-Country Scholarship Scheme 2026/27](https://scholarship.ptdf.gov.ng/) (Petroleum Technology Development Fund (Nigeria)), checked 2026-10-25
- [Mastercard Foundation Scholars, University of Cambridge 2026/27](https://mastercardfoundation.fund.cam.ac.uk/news/applications-20262027-academic-year-are-now-open) (Mastercard Foundation / University of Cambridge), checked 2026-10-25
- [Mastercard Foundation Graduate Scholarship, University of Toronto 2026/27](https://internationalexperience.utoronto.ca/) (Mastercard Foundation / University of Toronto), checked 2026-10-25
- [Mastercard Foundation Scholars, University of the Western Cape](https://www.uwc.ac.za/study/partnerships/mastercard-foundation-scholars-program) (Mastercard Foundation / UWC), checked 2026-10-25
- [Mastercard Foundation Scholars, University of Pretoria](https://www.up.ac.za/mastercard-foundation-scholarship-program) (Mastercard Foundation / University of Pretoria), checked 2026-10-25
- [Swedish Institute Scholarships for Global Professionals 2027/28](https://si.se/en/apply/scholarships/swedish-institute-scholarships-for-global-professionals/) (Swedish Institute), checked 2026-10-25
- [Stipendium Hungaricum 2027/28](https://abuja.mfa.gov.hu/en/articles/general-information-and-faq-of-the-stipendium-hungaricum-scholarship-program) (Hungary (Tempus Public Foundation)), checked 2026-10-25
- [Tⁿrkiye Scholarships 2027](https://turkiyeburslari.gov.tr/) (Tⁿrkiye (YTB)), checked 2026-10-25
- [Global Futures Scholarships for Africa (UK undergraduate)](https://www.ucas.com/explore/scholarships-and-bursaries/be6aed02-57fc-42f1-8aa8-d04e00192d42/global-futures-scholarships-for-africa---undergraduate) (Listed on UCAS (provider Not verified)), checked 2026-10-25
- [Northumbria International Scholarship (PGT, Nigerian applicants)](https://www.ucas.com/explore/scholarships-and-bursaries/522dd965-1128-4229-9214-e4660d0f9f98/2026-27-ug-international-scholarship-for-nigerian-applicants) (Northumbria University), checked 2026-10-25
- [NOHA Erasmus Mundus Joint Master's in International Humanitarian Action 2027û29](https://www.nohanet.org/masters) (NOHA Network (Erasmus Mundus)), checked 2026-10-25
- [University of Melbourne Graduate Research Scholarships](https://scholarships.unimelb.edu.au/awards/graduate-research-scholarships) (University of Melbourne), checked 2026-10-25
- [Mastercard Foundation Scholars, University of Edinburgh 2027/28](https://edinburgh-global.ed.ac.uk/mastercard-foundation-scholars-program/apply-for-a-scholarship/how-to-apply) (Mastercard Foundation / University of Edinburgh), checked 2026-10-25
- [Maastricht University NL-High Potential Scholarship 2027/28](https://www.maastrichtuniversity.nl/support/your-studies-begin/coming-maastricht-university-abroad/scholarships/maastricht-university) (Maastricht University), checked 2026-10-25
- [York University President's International Scholarship of Excellence (PISE)](https://futurestudents.yorku.ca/financial-support) (York University (Canada)), checked 2026-10-25
- [AfOx Graduate Scholarships (Oxford MBA) 2027/28](https://www.sbs.ox.ac.uk/oxford-experience/scholarships-and-funding/afox-graduate-scholarships) (Africa Oxford Initiative / Mastercard Foundation / Sa∩d Business School), checked 2026-10-25
- [NNPC/SNEPCo National University Scholarship 2026](https://www.shell.com.ng/careers/scholarships.html) (NNPC / SNEPCo (Shell Nigeria Exploration and Production Company)), checked 2026-10-27
- [BOC Sciences Chemistry Scholarship Program 2026](https://www.bocsci.com/chemistry-scholarship-program.html) (BOC Sciences (BOCSCI Inc.)), checked 2026-10-27
- [Mandela Washington Fellowship 2027](https://apply.mandelawashingtonfellowship.org/) (U.S. Department of State / IREX), checked 2026-10-25
- [MWF Reciprocal Exchange Component 2027](https://www.mandelawashingtonfellowship.org/2026/10/21/2027-reciprocal-exchange-component-application/) (U.S. Department of State / IREX), checked 2026-10-25
- [Millennium Fellowship Class of 2027](https://www.millenniumfellows.org/apply) (Millennium Campus Network & UN Academic Impact), checked 2026-10-25
- [Jim Leech Mastercard Foundation Fellowship on Entrepreneurship 2027](https://www.queensu.ca/innovationcentre/programs/jim-leech-mastercard-foundation-fellowship-entrepreneurship) (Queen's University (DDQIC) & Mastercard Foundation), checked 2026-10-27
- [Cowrywise Campus Ambassadors Program](https://ambassadors.cowrywise.com/register) (Cowrywise), checked 2026-10-01
- [Google Summer of Code (GSoC)](https://summerofcode.withgoogle.com/) (Google), checked 2026-10-25
- [MLH Fellowship](https://fellowship.mlh.com/) (Major League Hacking (MLH)), checked 2026-10-25
- [Outreachy Remote Internship](https://www.outreachy.org/) (Software Freedom Conservancy), checked 2026-10-25
- [Microsoft Leap Apprenticeship](https://leap.microsoft.com/) (Microsoft (Leap) with Africa Development Centre partners), checked 2026-10-25
- [Flutterwave Internship & Accelerator](https://flutterwave.com/us/careers) (Flutterwave), checked 2026-10-01
- [IBM Great Minds Student Internship](https://www.research.ibm.com/labs/africa/) (IBM Research Zurich / Africa), checked 2026-10-01
- [LPI Summer Intern Program in Planetary Science 2027](https://www.lpi.usra.edu/lpiintern/) (Lunar and Planetary Institute (USRA), Houston), checked 2026-10-27
- [MTN Global Graduate Development Program](https://www.mtn.ng/career/global-graduates/) (MTN Nigeria), checked 2026-10-25
- [Interswitch Graduate Trainee Programme](https://www.interswitchgroup.com/careers) (Interswitch Group), checked 2026-10-01
- [Access Bank Graduate Trainee Program](https://www.accessbankplc.com/careers) (Access Bank Plc), checked 2026-10-01
- [TotalEnergies Young Graduate Program](https://totalenergies.com/careers) (TotalEnergies Nigeria), checked 2026-10-01
- [Standard Bank Group Graduate Programme](https://www.standardbank.com/careers) (Standard Bank / Stanbic IBTC), checked 2026-10-01
- [KPMG Nigeria Graduate Trainee Programme](https://home.kpmg/ng/en/home/careers.html) (KPMG Nigeria), checked 2026-10-01
- [PwC Nigeria Graduate Trainee Programme](https://www.pwc.com/ng/en/careers.html) (PwC Nigeria), checked 2026-10-01
- [Volvo Group Graduate Programs (Sweden) 2027 intake](https://www.volvogroup.com/careers) (Volvo Group), checked 2026-10-27
- [American Impact Award](https://www.mandelawashingtonfellowship.org/2026/09/01/american-impact-award-application-now-open/) (U.S. Department of State / IREX), checked 2026-10-25
- [MTN Y'ellopreneur Grant & Loan Initiative](https://www.mtn.ng/foundation/) (MTN Foundation), checked 2026-10-01
- [Hult Prize (EF Hult Prize) 2026û27](https://www.hultprize.org/register) (Hult Prize Foundation / EF), checked 2026-10-25
- [Tony Elumelu Foundation Entrepreneurship Programme](https://www.tefconnect.com/) (Tony Elumelu Foundation), checked 2026-10-25
- [Data Science Nigeria AI Hackathon](https://datasciencenigeria.org/) (Data Science Nigeria (DSN)), checked 2026-10-01
- [Orange Social Venture Prize (OSVP)](https://poesa.orange.com/) (Orange Group), checked 2026-10-01
- [EQUALS in Tech Awards 2027](https://www.equalsintech.org/awards) (EQUALS Global Partnership (ITU, UN Women and others)), checked 2026-10-25
- [Commonwealth Foundation Grants Programme 2026-27](https://commonwealthfoundation.com/) (Commonwealth Foundation), checked 2026-10-27
- [ALX Africa Tech Upskilling Programmes](https://tech.alxafrica.com/) (ALX Africa & Mastercard Foundation), checked 2026-10-25
- [Ingressive For Good (I4G) Tech Training](https://ingressive.org/) (Ingressive For Good), checked 2026-10-01
- [She Code Africa Mentorship Program](https://shecodeafrica.org/) (She Code Africa), checked 2026-10-01
- [LSETF Tech Jobs Initiative](https://lsetf.ng/) (LSETF & Tech4Dev), checked 2026-10-01
- [IncuVersity (THE DO ╫ Anthropic)](https://doincuversity.ai/) (THE DO, in partnership with Anthropic), checked 2026-10-25
- [CMU-Africa Certificate in Artificial Intelligence for Africa](https://africa.engineering.cmu.edu/) (Carnegie Mellon University Africa), checked 2026-10-25
- [CS50x: Introduction to Computer Science](https://discover.edx.org/xgs/course/introduction-computer-science-harvardx-cs50x) (HarvardX / edX), checked 2026-10-25
- [GitHub Student Developer Pack](https://education.github.com/pack/join) (GitHub), checked 2026-10-25



## 10. Known limitations / next steps

### Limitations
- **Small dataset.** Opportunities are collected by hand from official pages, so the list is small (currently 72 number of records) and deadlines change. Always confirm details on the official page linked with each result.
- **Drafting records is unreliable.** In a test where the model drafted a record from an announcement already in our data (the MTN Science and Technology Scholarship), it got 4 of 8 fields right when compared with the record we collected from the official page. It correctly found the name, type and organisation, and correctly left the deadline empty. It got the eligibility rules, the levels, the courses and the link wrong: it put "No deadline stated" in the eligibility field, listed all seven levels instead of 300, 400 and graduate, filled the courses field with `["Computer Science", "300", "AI"]` instead of Science, Technology, Engineering, Mathematics and Medicine, and gave a different link from the official one. It also wrote the word "None" instead of leaving a field empty in an earlier test. Because of this, drafted records are never saved automatically: a person checks each one against the official page first.
- **Matching is simple.** Courses are matched by shared words (for example "Computer" in both "Computer Science" and "Computer Engineering"), so some related courses may be missed or wrongly matched. Interests are matched by keywords, not by meaning.
- **Nigeria-focused and English-only.** Other countries and languages are not supported.
- **No accounts or saved profiles.** Students enter their details each time.
- **Tested lightly.** Automated tests cover the matching rules and cleaning of model output. We tested the screen manually with 12 students.
- **Course and interest can conflict.** The course is treated as a requirement, and interests only rank results. A student whose interests differ from their course (for example a Nursing student interested in writing or software) often gets no matches, because the opportunities that fit their interest list other courses. Opportunities that fit through interest appear only under "Not eligible yet", and only when the interest words overlap with the opportunity's text. Courses are matched by shared words, so related courses such as Nursing and Medicine are not connected.

### Next steps
- Collect more verified opportunities, and add a way to flag expired or incorrect ones.
- Better matching using embeddings (meaning, not just keywords), and support for more details such as state of origin, CGPA and gender-specific schemes.
- Reminders before a deadline.
- Explanations in Pidgin, Yoruba, Igbo and Hausa.
- Try a larger open-weight model on a computer with more memory and compare the quality.
- Replace the JSON file with a database such as SQLite.
- Permanent hosting.
- Let students save a profile and track the opportunities they've applied for.
- **Interest-based matching.** Let students choose "match my course" or "match my interests", and use embeddings so related interests are matched by meaning (for example "writing" with "content creation" or "technical writing"). Also record, for each opportunity, whether students from other courses may apply, so the rule is not guessed from the course list.

## Licence
MIT, see `LICENSE`.
