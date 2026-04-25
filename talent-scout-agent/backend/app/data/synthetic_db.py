"""
Synthetic candidate database — ~60 realistic profiles across roles.
Loaded into memory at startup. Easily extensible: edit candidates.json.
"""
import json
import random
from pathlib import Path
from typing import List
from app.models.schemas import Candidate

DATA_FILE = Path(__file__).parent / "candidates.json"


def generate_candidates() -> List[dict]:
    """Generate a diverse, realistic candidate pool."""
    random.seed(42)

    first_names = ["Aarav", "Priya", "Arjun", "Diya", "Vihaan", "Ananya", "Reyansh", "Saanvi",
                   "Krishna", "Ishita", "Aditya", "Kavya", "Rohan", "Meera", "Karan", "Tara",
                   "Liam", "Emma", "Noah", "Olivia", "Ethan", "Sophia", "Lucas", "Mia",
                   "Mason", "Ava", "Logan", "Isabella", "James", "Charlotte", "Wei", "Yuki",
                   "Hiroshi", "Mei", "Carlos", "Sofia", "Diego", "Lucia", "Mateo", "Valentina",
                   "Aisha", "Omar", "Fatima", "Hassan", "Zara", "Rahul", "Neha", "Vikram",
                   "Pooja", "Sanjay", "Riya", "Akash", "Shreya", "Nikhil", "Anjali", "Manish",
                   "Sneha", "Varun", "Divya", "Arnav"]

    last_names = ["Sharma", "Patel", "Kumar", "Singh", "Gupta", "Reddy", "Nair", "Iyer",
                  "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
                  "Chen", "Wang", "Liu", "Tanaka", "Suzuki", "Kim", "Park", "Rodriguez",
                  "Hernandez", "Lopez", "Martinez", "Anderson", "Thomas", "Khan", "Ahmed",
                  "Rao", "Mehta", "Kapoor", "Joshi", "Verma", "Shah", "Desai", "Banerjee", "Das"]

    locations = [
        "Bangalore, India", "Hyderabad, India", "Mumbai, India", "Delhi NCR, India",
        "Pune, India", "Chennai, India", "Remote (India)",
        "San Francisco, CA", "New York, NY", "Seattle, WA", "Austin, TX", "Remote (US)",
        "London, UK", "Berlin, Germany", "Amsterdam, Netherlands", "Singapore",
        "Toronto, Canada", "Sydney, Australia", "Dubai, UAE"
    ]

    # Skill clusters by role
    role_templates = [
        {
            "role": "Senior Backend Engineer",
            "skills_pool": ["Python", "Django", "FastAPI", "PostgreSQL", "Redis", "Docker",
                            "Kubernetes", "AWS", "Microservices", "REST APIs", "GraphQL",
                            "Celery", "RabbitMQ", "Elasticsearch", "System Design"],
            "domains": ["fintech", "e-commerce", "saas"],
            "exp_range": (5, 12),
            "summary_tmpl": "Backend engineer with {y} years building scalable distributed systems. Strong in Python ecosystems and cloud-native architectures."
        },
        {
            "role": "Backend Engineer",
            "skills_pool": ["Node.js", "TypeScript", "Express", "MongoDB", "PostgreSQL",
                            "Docker", "AWS", "REST APIs", "Microservices", "Kafka", "Redis"],
            "domains": ["e-commerce", "saas", "edtech"],
            "exp_range": (2, 5),
            "summary_tmpl": "Backend developer with {y} years of experience in Node.js/TypeScript. Built APIs powering products with millions of users."
        },
        {
            "role": "Senior Frontend Engineer",
            "skills_pool": ["React", "TypeScript", "Next.js", "Redux", "Tailwind CSS",
                            "GraphQL", "Webpack", "Vite", "Jest", "Cypress", "Storybook",
                            "Accessibility", "Performance Optimization"],
            "domains": ["saas", "e-commerce", "media"],
            "exp_range": (5, 10),
            "summary_tmpl": "Frontend specialist with {y} years crafting performant React applications. Passionate about DX and design systems."
        },
        {
            "role": "Frontend Developer",
            "skills_pool": ["React", "JavaScript", "HTML", "CSS", "Tailwind CSS", "Vue.js",
                            "Redux", "REST APIs", "Git", "Webpack"],
            "domains": ["e-commerce", "saas", "edtech"],
            "exp_range": (1, 4),
            "summary_tmpl": "Frontend developer with {y} years building responsive web apps with React. Strong eye for UI detail."
        },
        {
            "role": "Full Stack Engineer",
            "skills_pool": ["React", "Node.js", "TypeScript", "Next.js", "PostgreSQL",
                            "MongoDB", "AWS", "Docker", "REST APIs", "GraphQL", "Tailwind CSS"],
            "domains": ["saas", "fintech", "edtech", "healthcare"],
            "exp_range": (3, 7),
            "summary_tmpl": "Full-stack engineer with {y} years across React + Node ecosystem. Comfortable owning features end-to-end."
        },
        {
            "role": "Machine Learning Engineer",
            "skills_pool": ["Python", "PyTorch", "TensorFlow", "scikit-learn", "Pandas",
                            "NumPy", "MLflow", "Kubernetes", "AWS SageMaker", "Docker",
                            "FastAPI", "SQL", "Spark", "Airflow"],
            "domains": ["fintech", "healthcare", "ai", "e-commerce"],
            "exp_range": (3, 8),
            "summary_tmpl": "ML engineer with {y} years deploying production ML systems. Experience across NLP, recsys, and CV domains."
        },
        {
            "role": "Senior ML Engineer",
            "skills_pool": ["Python", "PyTorch", "Transformers", "LLMs", "RAG", "LangChain",
                            "Vector Databases", "MLOps", "Kubernetes", "AWS", "GPU Optimization",
                            "Distributed Training", "Hugging Face"],
            "domains": ["ai", "fintech", "saas"],
            "exp_range": (6, 12),
            "summary_tmpl": "Senior ML engineer with {y} years. Recently focused on LLM applications and RAG systems at scale."
        },
        {
            "role": "Data Scientist",
            "skills_pool": ["Python", "SQL", "Pandas", "scikit-learn", "Statistics", "A/B Testing",
                            "Tableau", "Looker", "R", "Jupyter", "Causal Inference"],
            "domains": ["fintech", "e-commerce", "saas", "healthcare"],
            "exp_range": (2, 7),
            "summary_tmpl": "Data scientist with {y} years driving product decisions through experimentation and predictive modeling."
        },
        {
            "role": "DevOps Engineer",
            "skills_pool": ["Kubernetes", "Docker", "AWS", "Terraform", "Ansible", "CI/CD",
                            "Jenkins", "GitHub Actions", "Prometheus", "Grafana", "Linux",
                            "Bash", "Python", "Helm"],
            "domains": ["fintech", "saas", "e-commerce"],
            "exp_range": (3, 9),
            "summary_tmpl": "DevOps/SRE with {y} years of cloud infrastructure experience. Built reliable CI/CD pipelines and observability stacks."
        },
        {
            "role": "Mobile Engineer (iOS)",
            "skills_pool": ["Swift", "SwiftUI", "UIKit", "Objective-C", "Core Data", "Combine",
                            "REST APIs", "Firebase", "Xcode", "App Store"],
            "domains": ["e-commerce", "fintech", "media"],
            "exp_range": (2, 8),
            "summary_tmpl": "iOS engineer with {y} years shipping consumer apps. SwiftUI advocate."
        },
        {
            "role": "Mobile Engineer (Android)",
            "skills_pool": ["Kotlin", "Java", "Jetpack Compose", "Android SDK", "MVVM",
                            "Coroutines", "Room", "Retrofit", "Firebase"],
            "domains": ["e-commerce", "fintech", "media"],
            "exp_range": (2, 8),
            "summary_tmpl": "Android developer with {y} years of native app experience. Currently building with Jetpack Compose."
        },
        {
            "role": "Product Designer",
            "skills_pool": ["Figma", "Sketch", "User Research", "Prototyping", "Design Systems",
                            "UX Writing", "Accessibility", "Adobe Creative Suite"],
            "domains": ["saas", "e-commerce", "fintech"],
            "exp_range": (3, 9),
            "summary_tmpl": "Product designer with {y} years across B2B and consumer products. Strong systems thinker."
        },
        {
            "role": "Engineering Manager",
            "skills_pool": ["Leadership", "Hiring", "Mentorship", "System Design", "Agile",
                            "Python", "AWS", "Stakeholder Management", "Roadmapping"],
            "domains": ["saas", "fintech", "e-commerce"],
            "exp_range": (8, 15),
            "summary_tmpl": "Engineering manager with {y} years of experience, leading teams of 5-15 engineers across multiple product areas."
        },
        {
            "role": "Junior Software Engineer",
            "skills_pool": ["JavaScript", "Python", "Git", "HTML", "CSS", "React", "SQL"],
            "domains": ["saas", "edtech", "e-commerce"],
            "exp_range": (0, 2),
            "summary_tmpl": "Recent CS grad with {y} years of internship experience. Eager to learn and contribute to a strong engineering team."
        },
        {
            "role": "Site Reliability Engineer",
            "skills_pool": ["Linux", "Kubernetes", "Terraform", "AWS", "GCP", "Prometheus",
                            "Grafana", "Python", "Go", "Incident Response", "Observability"],
            "domains": ["fintech", "saas"],
            "exp_range": (4, 10),
            "summary_tmpl": "SRE with {y} years keeping high-traffic systems online. Strong incident response background."
        },
    ]

    companies_pool = ["Stripe", "Razorpay", "Zomato", "Swiggy", "Flipkart", "Amazon",
                      "Microsoft", "Google", "Meta", "Atlassian", "Shopify", "Airbnb",
                      "Uber", "Netflix", "Spotify", "Adobe", "Salesforce", "PayPal",
                      "Freshworks", "Zoho", "Postman", "InMobi", "Paytm", "PhonePe",
                      "BYJU's", "Unacademy", "Cred", "Groww", "Zerodha", "Notion"]

    educations = ["IIT Bombay", "IIT Delhi", "IIT Madras", "BITS Pilani", "NIT Trichy",
                  "IIIT Hyderabad", "VIT Vellore", "Stanford University", "MIT",
                  "UC Berkeley", "Carnegie Mellon", "University of Toronto",
                  "ETH Zurich", "TU Munich", "National University of Singapore",
                  "Delhi University", "Anna University"]

    candidates = []
    cid = 1

    # Generate 4 candidates per role template = 60 candidates
    for template in role_templates:
        for _ in range(4):
            years = random.randint(*template["exp_range"])
            num_skills = min(len(template["skills_pool"]), random.randint(5, 10))
            skills = random.sample(template["skills_pool"], num_skills)
            num_past = random.randint(1, 3)
            past_companies = random.sample(companies_pool, num_past + 1)
            current_company = past_companies[0]
            past = past_companies[1:]

            first = random.choice(first_names)
            last = random.choice(last_names)
            name = f"{first} {last}"

            domain = random.choice(template["domains"])

            candidate = {
                "id": f"cand_{cid:04d}",
                "name": name,
                "headline": f"{template['role']} at {current_company}",
                "location": random.choice(locations),
                "years_experience": years,
                "skills": skills,
                "current_role": template["role"],
                "current_company": current_company,
                "past_companies": past,
                "domains": [domain] + random.sample([d for d in ["fintech", "saas", "e-commerce",
                                                                  "healthcare", "edtech", "media", "ai"]
                                                     if d != domain], k=random.randint(0, 2)),
                "education": random.choice(educations),
                "summary": template["summary_tmpl"].format(y=years),
                "source": "synthetic",
                "profile_url": f"https://example.com/profiles/cand_{cid:04d}",
                "avatar_url": f"https://i.pravatar.cc/150?u=cand_{cid:04d}",
                "open_to_opportunities": random.random() > 0.15,
                "desired_salary": random.choice([None, "₹25-35 LPA", "₹40-55 LPA", "₹60-80 LPA",
                                                  "$120k-150k", "$150k-200k", "$200k-280k"]),
                "notice_period_days": random.choice([0, 15, 30, 60, 90])
            }
            candidates.append(candidate)
            cid += 1

    return candidates


def load_candidates() -> List[Candidate]:
    """Load candidates from disk, generating the file if it doesn't exist."""
    if not DATA_FILE.exists():
        candidates_data = generate_candidates()
        DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(DATA_FILE, "w") as f:
            json.dump(candidates_data, f, indent=2)
    else:
        with open(DATA_FILE, "r") as f:
            candidates_data = json.load(f)

    return [Candidate(**c) for c in candidates_data]


if __name__ == "__main__":
    cands = load_candidates()
    print(f"Loaded {len(cands)} candidates")
    print(f"Roles: {set(c.current_role for c in cands)}")
