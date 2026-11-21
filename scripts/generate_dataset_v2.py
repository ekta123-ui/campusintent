import random, re, csv, collections, os

rng = random.Random(7)
PER_INTENT = 320          # 16 intents x 320 = 5120 queries
MAX_VARIANTS_PER_BASE = 3  # cap on noisy variants of the same base sentence

SEM6 = [f"{o} semester" for o in ["1st", "2nd", "3rd", "4th", "5th", "6th"]]
SEM4 = SEM6[:4]
SEM8 = [f"{o} semester" for o in ["1st", "2nd", "3rd", "4th", "5th", "6th", "7th", "8th"]]
YR2 = ["1st year", "2nd year"]

IT_COMP = ["TCS", "Infosys", "Wipro", "Accenture", "Cognizant", "Capgemini", "Amazon", "Microsoft", "HCL", "Tech Mahindra", "IBM", "Zoho", "Adobe", "Mphasis"]
SEC_COMP = ["TCS", "Infosys", "Wipro", "Palo Alto Networks", "Quick Heal", "Deloitte", "KPMG", "Accenture", "HCL", "Cisco", "IBM", "Tech Mahindra"]
PHARMA = ["Sun Pharma", "Cipla", "Dr. Reddy's", "Lupin", "Zydus", "Apollo Pharmacy", "Biocon", "Mankind Pharma", "Cadila", "Alkem", "Torrent Pharma"]
HOTELS = ["Taj Hotels", "The Oberoi", "Marriott", "Hyatt", "ITC Hotels", "Radisson", "Hilton", "Lemon Tree", "Accor", "The Leela", "Sarovar Hotels"]
LAW = ["Cyril Amarchand Mangaldas", "AZB & Partners", "Khaitan & Co", "Trilegal", "Luthra & Luthra", "Shardul Amarchand", "Lakshmikumaran & Sridharan", "J. Sagar Associates"]
COMM = ["Deloitte", "EY", "KPMG", "PwC", "HDFC Bank", "ICICI Bank", "Axis Bank", "Kotak Mahindra Bank", "Grant Thornton", "Yes Bank", "Bajaj Finserv"]
SCI = ["Biocon", "Dr Lal PathLabs", "Sun Pharma", "Thermo Fisher", "SRL Diagnostics", "Cipla", "Tata 1mg", "Syngene", "Metropolis Healthcare"]

COURSES = {
 "MCA": dict(names=["MCA", "MCA", "M.C.A"], dept="Computer Applications", terms=SEM4,
    subjects=["Machine Learning", "Cloud Computing", "Software Engineering", "Artificial Intelligence", "Advanced DBMS", "Data Mining", "Natural Language Processing", "Big Data Analytics", "Python Programming", "Operating Systems"],
    roles=["software developer", "data analyst", "ML engineer", "full stack developer", "cloud engineer", "data scientist", "NLP engineer"], companies=IT_COMP),
 "BCA": dict(names=["BCA", "BCA", "B.C.A"], dept="Computer Applications", terms=SEM6,
    subjects=["Data Structures", "Python Programming", "DBMS", "Computer Networks", "Java", "Operating Systems", "Web Technologies", "C Programming", "Software Engineering", "Digital Electronics"],
    roles=["software developer", "web developer", "QA engineer", "support engineer", "junior data analyst", "frontend developer"], companies=IT_COMP),
 "B.Tech Cyber Security": dict(names=["B.Tech Cyber Security", "B.Tech in Cyber Security", "BTech Cyber Security", "B.Tech (Cyber Security)"], dept="Computer Science and Engineering", terms=SEM8,
    subjects=["Network Security", "Ethical Hacking", "Cryptography", "Digital Forensics", "Operating Systems", "Information Security", "Malware Analysis", "Computer Networks", "Cyber Law"],
    roles=["security analyst", "SOC analyst", "penetration tester", "network security engineer", "cyber forensics analyst", "information security associate"], companies=SEC_COMP),
 "B.Tech Web Development": dict(names=["B.Tech Web Development", "B.Tech in Web Development", "BTech Web Development", "B.Tech (Web Development)"], dept="Computer Science and Engineering", terms=SEM8,
    subjects=["React JS", "Node.js", "Web Technologies", "DBMS", "JavaScript", "UI/UX Design", "Cloud Computing", "Data Structures", "Software Engineering"],
    roles=["full stack developer", "frontend developer", "backend developer", "web developer", "UI developer", "software engineer"], companies=IT_COMP),
 "B.Tech AI & ML": dict(names=["B.Tech AI & ML", "B.Tech AI and ML", "BTech AI ML", "B.Tech in AI & ML", "B.Tech (AI & ML)"], dept="Computer Science and Engineering", terms=SEM8,
    subjects=["Machine Learning", "Deep Learning", "Natural Language Processing", "Python Programming", "Data Mining", "Computer Vision", "Artificial Intelligence", "Linear Algebra", "Reinforcement Learning"],
    roles=["AI engineer", "ML engineer", "data scientist", "data analyst", "NLP engineer", "computer vision engineer"], companies=IT_COMP),
 "B.Sc": dict(names=["B.Sc", "BSc", "B.Sc"], dept="Science", terms=SEM6,
    subjects=["Physics", "Chemistry", "Mathematics", "Zoology", "Botany", "Organic Chemistry", "Statistics", "Microbiology", "Biochemistry"],
    roles=["lab analyst", "research associate", "quality analyst", "data analyst", "lab technician"], companies=SCI),
 "M.Sc": dict(names=["M.Sc", "MSc", "M.Sc"], dept="Science", terms=SEM4,
    subjects=["Quantum Mechanics", "Organic Chemistry", "Analytical Chemistry", "Biochemistry", "Microbiology", "Advanced Mathematics", "Spectroscopy", "Molecular Biology"],
    roles=["research associate", "quality control analyst", "lab scientist", "data analyst", "clinical research associate"], companies=SCI),
 "B.Com": dict(names=["B.Com", "BCom", "B.Com (Hons)"], dept="Commerce", terms=SEM6,
    subjects=["Financial Accounting", "Business Law", "Taxation", "Cost Accounting", "Corporate Accounting", "Auditing", "Business Economics", "Banking and Insurance"],
    roles=["accountant", "tax analyst", "audit associate", "financial analyst", "banking associate", "accounts executive"], companies=COMM),
 "LLB": dict(names=["LLB", "LL.B", "LLB"], dept="Law", terms=SEM6,
    subjects=["Constitutional Law", "Criminal Law", "Contract Law", "Family Law", "Law of Torts", "Jurisprudence", "Law of Evidence", "Company Law", "Property Law"],
    roles=["legal associate", "paralegal", "corporate counsel trainee", "compliance officer", "litigation associate", "legal researcher"], companies=LAW),
 "Hotel Management": dict(names=["Hotel Management", "BHM", "Hotel Management", "B.Sc Hotel Management"], dept="Hotel Management", terms=SEM6 + ["7th semester", "8th semester"],
    subjects=["Food Production", "Front Office Operations", "Housekeeping Operations", "Food and Beverage Service", "Hospitality Management", "Nutrition", "Bakery and Confectionery", "Hotel Accountancy"],
    roles=["front office executive", "chef trainee", "guest relations executive", "F&B associate", "housekeeping supervisor", "management trainee"], companies=HOTELS),
 "B.Pharmacy": dict(names=["B.Pharmacy", "B.Pharma", "B.Pharm", "Pharmacy"], dept="Pharmacy", terms=SEM8,
    subjects=["Pharmacology", "Pharmaceutics", "Pharmaceutical Chemistry", "Pharmacognosy", "Human Anatomy and Physiology", "Pharmaceutical Analysis", "Medicinal Chemistry", "Pathophysiology"],
    roles=["pharmacist", "drug safety associate", "quality control analyst", "medical representative", "production executive", "clinical research associate"], companies=PHARMA),
 "D.Pharmacy": dict(names=["D.Pharmacy", "D.Pharm", "D.Pharma", "Diploma in Pharmacy"], dept="Pharmacy", terms=YR2,
    subjects=["Pharmacognosy", "Pharmaceutics", "Pharmacology", "Biochemistry", "Health Education", "Social Pharmacy", "Pharmaceutical Chemistry"],
    roles=["pharmacist", "pharmacy assistant", "store pharmacist", "dispensing pharmacist", "retail pharmacy executive"], companies=PHARMA),
}

S = {
    "month": ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"],
    "weekday": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"],
    "year_adm": ["2026", "2027", "2026-27", "2027-28"],
    "exam_type": ["mid-term", "end-semester", "practical", "viva", "supplementary", "backlog", "internal", "final"],
    "place": ["Gurgaon", "Sohna", "Faridabad", "Delhi", "Palwal", "Rewari", "Noida", "Manesar", "Badshahpur", "Nuh", "Ballabgarh", "Dwarka",
              "Bhiwadi", "Pataudi", "Rohtak", "Bahadurgarh", "Greater Noida", "Ghaziabad", "Alwar", "Hodal"],
    "facility": ["a gym", "Wi-Fi", "a laundry service", "a reading room", "hot water", "a study room", "an air-conditioned room",
                 "a common TV room", "power backup", "CCTV security", "a water cooler", "a medical room", "a geyser", "a cooler"],
    "scholarship": ["merit scholarship", "SC/ST scholarship", "sports quota scholarship", "EWS scholarship", "girl child scholarship",
                    "state government scholarship", "minority scholarship", "fee waiver scheme", "OBC scholarship",
                    "central sector scholarship", "need-based scholarship", "topper scholarship"],
    "doc": ["bonafide certificate", "transfer certificate", "migration certificate", "character certificate", "marksheet",
            "degree certificate", "ID card", "no-dues certificate", "provisional certificate", "fee receipt", "NOC",
            "course completion certificate", "internship letter", "backlog clearance certificate", "medium of instruction certificate", "attendance certificate"],
    "role_f": ["HOD", "Dean", "Principal", "Director", "Registrar", "class coordinator", "librarian", "program coordinator",
               "proctor", "warden", "exam controller", "student counsellor"],
    "office": ["Examination Cell", "Accounts Office", "Admission Office", "Training and Placement Cell", "Student Welfare Office",
               "Hostel Office", "Transport Office", "Library", "IT Helpdesk", "Scholarship Cell", "Sports Office"],
    "holiday": ["Diwali", "Holi", "Republic Day", "Independence Day", "Dussehra", "Raksha Bandhan", "Eid", "Christmas", "Gandhi Jayanti", "Guru Nanak Jayanti"],
    "event": ["annual day", "freshers party", "sports day", "tech fest", "cultural fest", "farewell", "orientation program",
              "convocation", "hackathon", "alumni meet", "college picnic", "science exhibition", "mock trial", "food festival"],
    "campus_place": ["auditorium", "seminar hall", "computer lab", "pharmacy lab", "moot court", "training kitchen", "sports ground", "bank branch",
                     "medical room", "parking area", "administrative block", "exam hall", "cybersecurity lab", "AI lab", "mock hotel room", "law library", "ATM"],
    "complaint_topic": ["bus delay", "canteen hygiene", "classroom cleanliness", "faculty absence", "parking issues", "washroom cleanliness", "water supply", "broken benches", "poor lighting in the lab",
                        "overcrowded buses", "mess food quality", "slow internet in the lab", "noise in the hostel", "AC not working in the classroom", "lab equipment shortage", "overpriced canteen items",
                        "wrong fee entry", "delay in scholarship credit", "misbehaviour by a staff member", "broken lift", "stray dogs on campus", "library seating shortage"],
    "floor": ["ground", "first", "second", "third", "fourth"],
    "dish": ["paneer butter masala", "biryani", "pasta", "chole bhature", "momos", "pizza", "dal tadka", "cake", "samosa", "maggi", "pancakes", "kheer", "sandwich", "burger", "rajma chawal", "paratha", "idli sambar", "cold coffee", "masala chai", "fried rice"],
    "meal": ["breakfast", "lunch", "dinner", "evening snacks"],
    "time": ["5 pm", "6 pm", "7 pm", "8 pm", "9 pm", "4 pm"],
    "ndays": ["2", "3", "4", "5", "7", "10"],
    "city": ["Delhi", "Mumbai", "Jaipur", "Pune", "Chandigarh", "Bengaluru", "Hyderabad", "Kolkata", "Lucknow", "Goa", "Shimla", "Chennai"],
    "country": ["Australia", "Canada", "Brazil", "Japan", "Germany", "Egypt", "France", "Argentina", "Norway", "Kenya", "Italy", "Peru"],
    "sport": ["cricket", "football", "hockey", "tennis", "kabaddi", "badminton", "IPL", "basketball"],
    "genre": ["comedy", "thriller", "romantic", "horror", "action", "sci-fi", "animated", "sports"],
    "gadget": ["iPhone", "a gaming laptop", "a smartwatch", "PlayStation 5", "AirPods", "a 4K TV", "a tablet", "a DSLR camera"],
    "topic": ["space exploration", "climate change", "electric cars", "cryptocurrency", "the Olympics", "ancient Egypt", "dinosaurs", "football", "the ocean", "moon landing"],
    "language": ["French", "Spanish", "German", "Japanese", "Tamil", "Punjabi", "Korean", "Italian"],
    "thing": ["mountain", "building", "bridge", "river", "waterfall", "tower"],
    "word": ["serendipity", "ephemeral", "ubiquitous", "nostalgia", "ambiguous", "resilient", "eloquent", "pragmatic"],
}

def disp(key):
    return rng.choice(COURSES[key]["names"])

def fill(t):
    names = list(dict.fromkeys(re.findall(r"{(\w+)}", t)))
    hidden = rng.choice(list(COURSES))
    ctx, used_course = {}, None
    if "course" in names:
        ctx["course"] = disp(hidden)
        used_course = hidden
    for n in names:
        if n in ctx:
            continue
        c = COURSES[hidden]
        if n == "course2":
            ctx[n] = disp(rng.choice([k for k in COURSES if k != hidden]))
        elif n == "dept":
            ctx[n] = c["dept"]
        elif n == "subject":
            ctx[n] = rng.choice(c["subjects"])
        elif n == "term":
            ctx[n] = rng.choice(c["terms"])
        elif n == "role":
            ctx[n] = rng.choice(c["roles"])
        elif n == "company":
            ctx[n] = rng.choice(c["companies"])
        elif n == "date":
            ctx[n] = f"{rng.randint(1, 28)} {rng.choice(S['month'])}"
        elif n == "pct":
            ctx[n] = str(rng.randint(40, 90))
        elif n == "income":
            ctx[n] = str(rng.randint(1, 8))
        elif n == "budget":
            ctx[n] = rng.choice(["10000", "15000", "20000", "30000", "50000"])
        elif n == "city2":
            ctx[n] = rng.choice([x for x in S["city"] if x != ctx.get("city")])
        elif n == "place2":
            ctx[n] = rng.choice([x for x in S["place"] if x != ctx.get("place")])
        elif n == "price":
            ctx[n] = str(rng.choice([20, 30, 40, 50, 60, 80, 100, 120]))
        else:
            ctx[n] = rng.choice(S[n])
    return t.format(**ctx), used_course

EN = {
"Admission": [
 "What is the last date to apply for {course} admission?", "How can I apply for {course} admission in {year_adm}?",
 "What is the eligibility criteria for {course}?", "Is the admission form for {course} open?",
 "Which entrance exam is required for {course} admission?", "What documents are required at the time of admission to {course}?",
 "Is there a lateral entry option for {course}?", "How many seats are available in {course}?",
 "What is the cut-off for {course} admission?", "Can I take admission in {course} with {pct}% marks in 12th?",
 "When will the counselling for {course} start?", "Is direct admission available for {course}?",
 "How do I check my admission status for {course}?", "Where can I download the {course} admission form?",
 "What is the selection process for {course}?", "Can I change my course from {course} to {course2} after admission?",
 "Is spot admission available for {course}?", "When is the merit list for {course} going to be released?",
 "Do I need to appear for an entrance test for {course} admission?", "Can I apply for {course} admission online?",
 "What is the minimum percentage needed for {course} admission?", "Is migration allowed for {course} admission from another university?",
 "When does the {course} admission process begin for {year_adm}?", "Is {course} admission based on merit or entrance score?",
 "I want to join {course}, what should I do first?", "Can I apply for both {course} and {course2}?",
 "How long is the {course} program?", "Which subjects do I need in 12th to get into {course}?",
 "Is {course} approved by the university and the regulatory council?", "What is the intake capacity of {course}?",
],
"Fees": [
 "What is the total fee for {course}?", "What is the last date to pay the {term} fee?",
 "How can I pay my college fee online?", "Is there a late fee fine if I pay after {date}?",
 "Can I pay the {course} fee in installments?", "What is the hostel fee per year?",
 "How much is the exam fee for {term}?", "Where can I get my fee receipt?",
 "My fee payment failed but the money was deducted, what should I do?", "Is the caution money refundable?",
 "What is the fee structure for {course} for {year_adm}?", "Can I pay the fee through UPI?",
 "How do I get a refund of my fees after cancelling admission?", "Is there any fee hike this year for {course}?",
 "Do I need to pay the transport fee separately?", "What is the fee for the {exam_type} exam?",
 "Can I get a fee extension till {date}?", "What are the fee payment modes accepted by the college?",
 "Is the lab fee included in the tuition fee of {course}?", "How much is the registration fee for {course}?",
 "What is the one-time admission fee for {course}?", "Can I pay my {term} fee by demand draft?",
 "How much is the development fee per semester?", "Where do I pay the fee, online or at the accounts office?",
 "What is the annual fee of {course} including the hostel?", "Is the {course} practical or training fee charged separately?",
 "What is the mess fee for hostel students?", "How much do I have to pay for the bus facility per semester?",
],
"Exam_Results": [
 "When will the {term} results be declared?", "What is the date sheet for the {exam_type} exams?",
 "When do the {term} exams start?", "How can I check my result online?",
 "How do I apply for re-evaluation of {subject}?", "Where can I download the admit card for the {exam_type} exam?",
 "What is the passing marks criteria for {subject}?", "How do I apply for a supplementary exam in {subject}?",
 "Is the {subject} exam going to be open book?", "What is the syllabus for the {subject} {exam_type} exam?",
 "My roll number is missing from the exam list, what should I do?", "What is the exam pattern for {subject}?",
 "When will the practical exam for {subject} be conducted?", "How are internal marks calculated for {subject}?",
 "Can I apply for a re-exam if I missed the {subject} paper?", "When will the exam center for {term} be announced?",
 "How can I see my {subject} answer sheet?", "What is the grading system followed in the {course} program?",
 "Has the {exam_type} exam been postponed?", "Will the {subject} result be out before {month}?",
 "How is the CGPA calculated for {course}?", "Is the {subject} paper going to be objective or descriptive?",
 "Where can I get the previous year question papers for {subject}?", "Where can I check my {term} marks?",
 "When will the {course} viva voce exam be held?", "What is the passing criteria for the {course} final project?",
],
"Timetable_Schedule": [
 "What is the class timetable for {term} {course}?", "Is there a class on {weekday}?",
 "What time does the first lecture start on {weekday}?", "When does the {term} begin?",
 "Is the college closed on {holiday}?", "What are the college working hours?",
 "When is the lab session for {subject}?", "Has the {subject} class been rescheduled?",
 "Where can I find the academic calendar?", "When are the summer vacations starting?",
 "Is the {subject} lecture cancelled today?", "Which room is the {subject} class in?",
 "What is the lunch break timing?", "When is the next holiday?",
 "Will there be an extra class for {subject} on {weekday}?", "When is the {event} scheduled?",
 "What is the schedule for the {event}?", "On which date does the winter break start?",
 "Is there a holiday on {date}?", "What is the schedule of the {subject} lectures this week?",
 "Will the college be open on {holiday}?", "At what time does the {event} begin?",
 "Is the {event} on {weekday} or {weekday}?", "What time do the afternoon classes end on {weekday}?",
 "When does the industrial training or internship for {course} start?", "Is the {course} lab scheduled on {weekday}?",
],
"Hostel_Accommodation": [
 "Is hostel accommodation available for {course} students?", "How do I apply for a hostel room?",
 "What is the hostel in-time for girls?", "Does the hostel have {facility}?",
 "Can I change my hostel room?", "What are the hostel rules regarding visitors?",
 "Are there single occupancy rooms in the hostel?", "What is the hostel check-out procedure during vacations?",
 "Is Wi-Fi available in the hostel rooms?", "How can I report a maintenance issue in my hostel room?",
 "How far is the hostel from the main campus?", "Is laundry service provided in the hostel?",
 "How can I book a hostel room for {year_adm}?", "Is there any hostel for {course} first-year students?",
 "Is there a separate hostel for girls and boys?", "How many students stay in one hostel room?",
 "Are electric kettles allowed in the hostel?", "Can I keep a laptop and a mini fridge in my hostel room?",
 "How do I contact the hostel warden?", "What is the hostel allotment process for {course} students?",
 "Do I need to submit a local guardian form for the hostel?", "Can I leave the hostel on weekends?",
 "What is the hostel curfew time?", "Is hostel accommodation guaranteed for {course} students in {year_adm}?",
 "Can I stay in the hostel during the {exam_type} exam break?", "Is there a hostel for students doing {course} internships?",
],
"Transport_Bus": [
 "Is bus facility available from {place}?", "What are the bus timings from {place} to college?",
 "How do I get a bus pass?", "Is there a bus stop near {place}?",
 "Which route does the college bus take via {place}?", "Are parking facilities available for students' bikes?",
 "Does the college provide a cab service from {place}?", "Is there a college bus from {place} on {weekday}?",
 "What is the last bus timing from the campus to {place}?", "How do I register for the college bus?",
 "Is the bus service available during the {exam_type} exams?", "How do I contact the transport office?",
 "What time does the morning bus leave from {place}?", "Can I change my bus stop from {place} to {place2}?",
 "Is there a separate bus for girls?", "Is there a shuttle between the campus and the metro station?",
 "How many buses run from {place} every day?", "Does the bus run on {weekday} for {course} students?",
 "Is the bus pass valid for the whole year?", "How do I renew my bus pass?",
 "Does the college bus come to {place} in the evening?", "What is the pick-up time at {place} for the 9 am lecture?",
 "Is there any bus from {place} for the practical batch?", "Can I use the college bus only for one-way travel?",
 "Is there a bus for students living in {place}?", "Where do I park my car on the campus?",
],
"Placement": [
 "Which companies visit the campus for {role} roles?", "What was the highest package offered last year?",
 "What is the average package for {course} students?", "When does the placement drive for {company} start?",
 "How do I register for campus placements?", "What is the eligibility criteria for {company} campus recruitment?",
 "Does the college provide internship opportunities for {course}?", "Is there any training for placement preparation?",
 "How many students got placed in {company} last year?", "What is the placement percentage of {course}?",
 "Can I sit for placements if I have a backlog?", "How do I contact the placement cell?",
 "Will there be mock interviews before the {company} drive?", "What is the minimum CGPA required for placements?",
 "Are there any off-campus drive updates for {role}?", "How can I upload my resume to the placement portal?",
 "Does {company} hire {course} students?", "When will the pre-placement talk for {company} be held?",
 "What skills do I need for a {role} job through campus placement?", "Is the placement cell offering aptitude test training?",
 "Is {company} coming to the campus this year?", "How many rounds are there in the {company} recruitment process?",
 "Are there any {role} openings through the placement cell?", "Does the placement cell help with resume building?",
 "What was the median package for {course} last year?", "Which companies recruited {course} students last year?",
],
"Scholarship": [
 "Am I eligible for the {scholarship}?", "How do I apply for the {scholarship}?",
 "What is the last date to apply for the {scholarship}?", "What documents are needed for the {scholarship}?",
 "How much amount is given under the {scholarship}?", "When will the {scholarship} amount be credited to my account?",
 "Is there any scholarship for {course} students?", "What is the minimum percentage required for the {scholarship}?",
 "Can I apply for more than one scholarship?", "Where can I check the status of my {scholarship} application?",
 "Who should I contact for scholarship related queries?", "Is the {scholarship} renewed every year?",
 "Does the college offer a scholarship for toppers in {course}?", "My scholarship has not been received yet, what should I do?",
 "Are there any scholarships for students with a family income below {income} lakh?",
 "Is the {scholarship} available for {term} students too?", "What is the procedure to renew my {scholarship}?",
 "Is the {scholarship} open for {course} students in {year_adm}?", "How are students selected for the {scholarship}?",
 "Will I lose my {scholarship} if my marks drop below {pct}%?", "Can I get the {scholarship} along with a fee waiver?",
],
"Documents_Certificates": [
 "How do I apply for a {doc}?", "How many days does it take to get a {doc}?",
 "Where can I collect my {doc}?", "What is the procedure to get a {doc}?",
 "I lost my {doc}, how can I get a duplicate?", "Can I apply for a {doc} online?",
 "Who signs the {doc}?", "What documents are needed to get a {doc}?",
 "My {doc} has a wrong spelling of my name, how can I correct it?", "Is a {doc} required for a bank loan?",
 "Can I get an urgent {doc} today?", "Where can I download the application form for a {doc}?",
 "How do I upload my documents on the student portal?", "What is the process to submit original documents after admission?",
 "Can I submit self-attested copies instead of originals?", "When will my {doc} be ready?",
 "Can someone else collect my {doc} on my behalf?", "Is a {doc} issued to {course} students after the {term}?",
 "Which office issues the {doc}?", "Do I need a {doc} for my passport application?",
],
"Faculty_Department": [
 "Who is the {role_f} of the {dept} department?", "How can I contact the {role_f} of {dept}?",
 "What is the email id of the {office}?", "Where is the {dept} department located?",
 "Who teaches {subject} for the {term}?", "What are the office hours of the {role_f}?",
 "Can I meet the {role_f} without an appointment?", "Which professor handles {subject}?",
 "What is the phone number of the {office}?", "How can I take an appointment with the {role_f}?",
 "Who is my class coordinator for {course} {term}?", "Which faculty guides the final year projects in {dept}?",
 "In which building is the {dept} department?", "Are there any new faculty joining the {dept} department?",
 "Who is the mentor assigned to {course} students?", "Which faculty member is the {subject} lab in-charge?",
 "On which floor is the {role_f}'s office?", "Is the {role_f} available on {weekday}?",
 "What qualifications do the {dept} faculty members have?", "Who is the head of the {office}?",
 "What are the working hours of the {office}?", "Does the {dept} department have industry experts as visiting faculty?",
],
"Cafeteria_Food": [
 "What are the cafeteria timings?", "What is on the cafeteria menu today?", "Is the canteen open on {weekday}?",
 "Does the cafeteria serve {dish}?", "What is the price of {dish} in the canteen?", "Is there a pure veg counter in the cafeteria?",
 "Can I pay at the canteen using UPI?", "Is the canteen open after {time}?", "Is there a juice or coffee shop on the campus?",
 "Where is the cafeteria located in the campus?", "Is lunch available for day scholars in the mess?", "Is there a Jain food option in the cafeteria?",
 "How do I get a meal coupon for the canteen?", "What snacks are available in the canteen during the break?",
 "Is there a food court near the {dept} building?", "What is the mess menu for today?", "Is the hostel mess food veg only?",
 "Can day scholars use the hostel mess?", "What time is {meal} served in the mess?", "Is {dish} available in the canteen on {weekday}?",
 "Is the training restaurant of the hotel management department open for lunch?", "Is there a bakery counter in the cafeteria?",
 "Is the canteen open during the {exam_type} exams?", "Is there a monthly meal plan for non-hostel students?",
 "How much does a {meal} thali cost in the cafeteria?", "Does the mess provide {meal} on {weekday}?", "Is there a Wi-Fi or seating area in the cafeteria?",
],
"Location_Directions": [
 "Where is the college located?", "What is the address of the college?", "How do I reach the college from {place}?",
 "Where is the {dept} department building in the campus?", "What is the nearest metro station to the college?",
 "How far is the college from {place}?", "Is there a Google Maps location for the campus?", "Which is the nearest railway station to the college?",
 "Where is the admission office located?", "Where is the main gate of the college?", "Which gate should I use to reach the {dept} block?",
 "Where is the {campus_place} located?", "Which floor is the {campus_place} on?", "How do I get to the {campus_place} from the main gate?",
 "Is there a campus map available?", "What are the nearest landmarks to the college?", "Is the college near {place}?",
 "Can I get an auto or a cab from {place} to the college?", "What is the pin code of the college?",
 "How much time does it take to reach the college from {place} by road?", "Is the {campus_place} in the same building as the {dept} department?",
 "Which is the nearest bus stand to the college?", "Is there a shared auto from {place} to the college gate?",
 "How can I reach the college from {place} by public transport?", "Is the {campus_place} open to {course} students?",
],
"Library_Facilities": [
 "How many books can I issue from the library at a time?", "What is the fine for returning a library book late?",
 "Does the library have books on {subject}?", "How do I renew an issued book?", "Can I access e-journals from the library?",
 "How do I get a library card?", "Is there a digital library with {subject} e-books?", "Can I borrow reference books for the {term}?",
 "Is the reading hall open during the {exam_type} exams?", "Can I use the library computers for research?",
 "How long can I keep a book issued from the library?", "How do I request a new book for the library?",
 "Does the library keep previous year question papers for {subject}?", "Can I get a photocopy of pages from a library book?",
 "I lost a library book, what should I do?", "How do I become a member of the library?",
 "Which journals does the library subscribe to for {course}?", "What are the library opening hours?",
 "Is the library open on {weekday}?", "Is there a separate section for {course} books in the library?",
 "Does the library have a copy of the {subject} textbook?", "Can I reserve a book for {subject} online?", "Is the library open on Sundays during exams?",
],
"Attendance_Leave": [
 "What is the minimum attendance required for {course}?", "How can I check my attendance online?",
 "How do I apply for medical leave?", "My attendance is below {pct}%, what can I do?", "Is there any condonation for shortage of attendance?",
 "How do I apply for leave for {ndays} days?", "Will I get attendance for the {event}?", "Can I get duty leave for participating in the {event}?",
 "Who marks the attendance for the {subject} lab?", "Is biometric attendance compulsory?", "How is attendance counted for {subject} practicals?",
 "Where can I submit my leave application?", "Can my attendance be corrected if it was marked wrongly in {subject}?",
 "What is the attendance percentage needed for the {exam_type} exam?", "Is there a penalty for low attendance in {term}?",
 "Can I get attendance relaxation for an internship?", "How do I request leave for a family function?",
 "Will the attendance of the {subject} class be updated on the portal?", "Do absent days during the {event} count against my attendance?",
 "What is the attendance rule for {course} industrial training?", "How many leaves are allowed in a {term}?",
],
"Complaint_Support": [
 "The college Wi-Fi is not working, who should I contact?", "How do I reset my student portal password?",
 "I cannot log in to the student portal, what should I do?", "How do I file a complaint against ragging?",
 "Where can I submit a grievance?", "The projector in the {dept} classroom is not working, whom should I report to?",
 "How can I report a broken fan in the classroom?", "Is there an anti-ragging helpline number?",
 "How do I lodge a complaint about {complaint_topic}?", "Who handles student grievances in the college?",
 "Is there a suggestion box for students?", "How do I get my ERP login credentials?",
 "My college email id is not created yet, how do I get it?", "How can I report a lost item on campus?",
 "The water cooler on the {floor} floor is not working, whom should I inform?", "How do I contact the IT helpdesk?",
 "My portal shows wrong details, how do I get them corrected?", "Where is the Internal Complaints Committee office?",
 "Can I submit my complaint about {complaint_topic} online?", "Whom should I report to about {complaint_topic}?",
 "The {campus_place} computers are not working, who should I tell?", "Is there a helpline number for student safety?",
 "How do I complain about {complaint_topic} to the {office}?", "Who resolves complaints related to {complaint_topic}?",
 "I have an issue with {complaint_topic}, where should I write?", "Can I raise a ticket for {complaint_topic}?",
 "How long does the college take to resolve a complaint about {complaint_topic}?", "Is there an online form to report {complaint_topic}?",
 "The AC in the {campus_place} is not working, whom should I inform?", "Whom do I contact if the {campus_place} is locked during my class?",
 "I want to report {complaint_topic} in the {dept} block", "Can I submit an anonymous complaint about {complaint_topic}?",
 "Where is the grievance box for the {dept} department?", "My ID card does not scan at the {campus_place}, whom should I contact?",
 "The Wi-Fi in the {campus_place} is very slow, who handles this?", "My {subject} lab login is not working, who can help?",
 "Who do I report to if the {campus_place} lights are not working on the {floor} floor?", "How can I track the status of my complaint about {complaint_topic}?",
],
"Out_of_Scope": [
 "What is the weather like in {city} today?", "Who won the {sport} match yesterday?", "Can you recommend a good {genre} movie?",
 "How do I make {dish} at home?", "What is the capital of {country}?", "Tell me a joke", "What is the price of {gadget}?",
 "How do I book a flight to {city}?", "What is the latest news about {topic}?", "Who is the prime minister of {country}?",
 "How is the stock market doing today?", "Suggest a good restaurant in {city}", "What is the meaning of {word}?",
 "Can you sing a song for me?", "How to lose weight fast?", "What time is it in {city}?", "Translate good morning into {language}",
 "How do I book a train ticket from {city} to {city2}?", "What is the best smartphone under {budget} rupees?",
 "Tell me a fun fact about {topic}", "Write a poem about {topic}", "What should I gift my friend on her birthday?",
 "Is it going to rain in {city} tomorrow?", "How many calories are in {dish}?", "Which is the tallest {thing} in the world?",
 "What is the best way to learn {language}?", "Who is the best {sport} player right now?", "Can you tell me a bedtime story about {topic}?",
 "How far is {city} from {city2}?", "What are the top tourist places in {city}?",
],
}

HI = {
"Admission": ["{course} mein admission kaise milega?", "{course} admission ki last date kya hai?", "kya {course} ke liye entrance exam dena padega?",
              "{course} admission form kab tak bharna hai?", "mujhe {course} mein admission lena hai, eligibility kya hai?", "{course} ki seats kitni hai?"],
"Fees": ["{course} ki fees kitni hai?", "fees kab tak jama karni hai?", "kya fees installment mein de sakte hain?",
         "fee receipt kahan se milegi?", "hostel ki fees kitni lagegi?", "{term} ki fees kab bharni hai?"],
"Exam_Results": ["{term} ka result kab aayega?", "{exam_type} exam ki date sheet kab aayegi?", "admit card kahan se download karu?",
                 "{subject} ka re-evaluation kaise karwau?", "supplementary exam ka form kab bharna hai?", "{subject} ka paper kaisa aayega?"],
"Timetable_Schedule": ["kal {subject} ki class hai kya?", "{weekday} ko college khula hai kya?", "{term} kab shuru hoga?",
                       "{subject} ka lab kab hai?", "{event} kab hoga?", "{holiday} pe college band rahega kya?"],
"Hostel_Accommodation": ["hostel mein room kaise milega?", "hostel mein wifi hai kya?", "hostel ka in-time kya hai?",
                         "hostel mein single room milta hai kya?", "{course} walon ke liye hostel hai kya?", "hostel warden se kaise milu?"],
"Transport_Bus": ["{place} se bus chalti hai kya?", "bus pass kaise banwau?", "{place} se college tak bus ka time kya hai?",
                  "college bus ka registration kaise hota hai?", "kya {place} ke liye shaam ko bus milegi?", "bus ka route kya hai?"],
"Placement": ["{company} placement drive kab hai?", "is saal highest package kitna gaya?", "placement ke liye register kaise karu?",
              "kya backlog wale placement mein baith sakte hain?", "{course} ka average package kitna hai?", "{company} mein kitne bacche select hue?"],
"Scholarship": ["{scholarship} ke liye apply kaise karu?", "scholarship ka paisa kab aayega?", "scholarship ke liye kaun se documents chahiye?",
                "kya main {scholarship} ke liye eligible hoon?", "scholarship ki last date kab hai?", "{scholarship} renew kaise hoti hai?"],
"Documents_Certificates": ["{doc} kaise milega?", "mera {doc} kho gaya hai, duplicate kaise banwau?", "{doc} banne mein kitne din lagte hain?",
                           "{doc} ke liye application kahan dena hai?", "kya {doc} online apply kar sakte hain?", "{doc} kaun sign karta hai?"],
"Faculty_Department": ["{dept} ke HOD kaun hain?", "{role_f} se milne ke liye appointment kaise lu?", "{subject} kaun padhata hai?",
                       "{dept} ka office kahan hai?", "{office} ka phone number kya hai?", "{role_f} kab milte hain?"],
"Cafeteria_Food": ["canteen kitne baje khulta hai?", "aaj mess mein kya bana hai?", "canteen mein {dish} milta hai kya?",
                   "{meal} ka time kya hai?", "canteen mein UPI se payment ho jata hai kya?", "{dish} ka rate kya hai canteen mein?"],
"Location_Directions": ["college ka address kya hai?", "{place} se college kaise pahunchu?", "nearest metro station kaun sa hai?",
                        "{campus_place} kahan hai?", "college {place} se kitni door hai?", "main gate kahan hai?"],
"Library_Facilities": ["library kitne baje tak khuli rehti hai?", "library se ek baar mein kitni books mil sakti hain?", "library card kaise banega?",
                       "{subject} ki book library mein hai kya?", "book late return karne ka fine kitna hai?", "e-journals kaise access karu?"],
"Attendance_Leave": ["{course} mein attendance kitni chahiye?", "meri attendance kam hai, kya karu?", "leave application kahan dena hai?",
                     "medical leave kaise lete hain?", "attendance online kaise check karu?", "{event} ki attendance milegi kya?"],
"Complaint_Support": ["college ka wifi nahi chal raha, kisse baat karu?", "student portal ka password kaise reset karu?", "shikayat kahan darj karaun?",
                      "{complaint_topic} ki complaint kahan karni hai?", "IT helpdesk ka number kya hai?", "ragging ki complaint kaise karein?"],
"Out_of_Scope": ["aaj {city} ka mausam kaisa hai?", "{sport} ka match kaun jeeta?", "koi acchi {genre} movie batao",
                 "{dish} kaise banate hain?", "ek joke sunao", "{city} mein ghumne ki best jagah kaun si hai?"],
}

SHORT = {"please": "pls", "when": "whn", "what": "wat", "semester": "sem", "application": "appln", "information": "info",
         "certificate": "certi", "you": "u", "are": "r", "tomorrow": "tmrw", "admission": "admn", "department": "dept",
         "and": "n", "how": "hw", "which": "wch", "available": "avlbl", "number": "no", "college": "clg", "cafeteria": "cafe",
         "hostel": "hstl", "library": "lib", "kab": "kb", "kya": "kia"}

def casual(q):
    q = q.lower()
    q = re.sub(r"[,.]", "", q)
    if rng.random() < 0.6:
        q = q.replace("?", "")
    return q.strip()

def shortform(q):
    q = casual(q)
    out = []
    for w in q.split():
        core = w.strip("?")
        if core in SHORT and rng.random() < 0.8:
            out.append(SHORT[core] + ("?" if w.endswith("?") else ""))
        else:
            out.append(w)
    return " ".join(out)

def typo(q):
    q = casual(q)
    words = q.split()
    idx = [i for i, w in enumerate(words) if len(w) >= 5 and w.isalpha()]
    if not idx:
        return q
    for i in rng.sample(idx, k=min(len(idx), rng.choice([1, 1, 2]))):
        w = words[i]
        p = rng.randint(1, len(w) - 2)
        k = rng.choice(["swap", "drop", "dup"])
        if k == "swap":
            w = w[:p] + w[p + 1] + w[p] + w[p + 2:]
        elif k == "drop":
            w = w[:p] + w[p + 1:]
        else:
            w = w[:p] + w[p] + w[p:]
        words[i] = w
    return " ".join(words)

def key(q):
    return re.sub(r"[^a-z0-9 ]", "", q.lower()).strip()

rows, seen = [], set()
for intent in EN:
    n, attempts = 0, 0
    base_count = collections.Counter()
    while n < PER_INTENT and attempts < 400000:
        attempts += 1
        if rng.random() < 0.12:
            q, course = fill(rng.choice(HI[intent]))
            lang = "hinglish"
            style = "hinglish" if rng.random() < 0.6 else "hinglish_casual"
            if style == "hinglish_casual":
                q = casual(q)
        else:
            q, course = fill(rng.choice(EN[intent]))
            lang = "english"
            style = rng.choices(["formal", "casual", "shortform", "typo"], weights=[35, 25, 18, 22])[0]
            base = key(q)
            if base_count[base] >= MAX_VARIANTS_PER_BASE:
                continue
            base_count[base] += 1
            q = {"formal": lambda x: x, "casual": casual, "shortform": shortform, "typo": typo}[style](q)
        k = key(q)
        if k in seen:
            continue
        seen.add(k)
        rows.append({"query": q, "intent": intent, "language": lang, "style": style, "course": course or ""})
        n += 1
    assert n == PER_INTENT, (intent, n)

rng.shuffle(rows)
by_intent = collections.defaultdict(list)
for i, r in enumerate(rows):
    by_intent[r["intent"]].append(i)
for intent, idxs in by_intent.items():
    cut1, cut2 = int(len(idxs) * 0.70), int(len(idxs) * 0.85)
    for j, i in enumerate(idxs):
        rows[i]["split"] = "train" if j < cut1 else ("val" if j < cut2 else "test")

intent_ids = {k: i for i, k in enumerate(EN)}
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "raw", "campus_intent_dataset_v2.csv")
with open(out, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["id", "query", "intent", "intent_id", "course", "language", "style", "split"])
    for i, r in enumerate(rows, 1):
        w.writerow([i, r["query"], r["intent"], intent_ids[r["intent"]], r["course"], r["language"], r["style"], r["split"]])
print("written", len(rows), out)
