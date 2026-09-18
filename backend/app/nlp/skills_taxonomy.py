"""
Skills taxonomy for JobMatch BD.

Maps a canonical skill name to a list of aliases/variants that people
actually type in CVs and that employers use in postings. This is what
the PhraseMatcher in extractor.py searches for.

This list is intentionally focused on CS/software/data roles for the
MVP (see README "Scope" section). Extend it category by category as
you add more job types.
"""

SKILLS_TAXONOMY: dict[str, list[str]] = {
    # Languages
    "Python": ["python", "python3"],
    "C#": ["c#", "csharp", "c-sharp"],
    "C++": ["c++", "cpp"],
    "Java": ["java"],
    "JavaScript": ["javascript", "js", "es6", "ecmascript"],
    "TypeScript": ["typescript", "ts"],
    "Go": ["golang", "go lang"],
    "R": ["r language", "r programming"],
    "SQL": ["sql", "structured query language"],

    # Web / backend frameworks
    "ASP.NET Core": ["asp.net core", "asp.net", "aspnet core", "aspnetcore"],
    "Django": ["django"],
    "Flask": ["flask"],
    "FastAPI": ["fastapi", "fast api"],
    "Node.js": ["node.js", "nodejs", "node js"],
    "Express.js": ["express.js", "expressjs", "express js"],
    "Spring Boot": ["spring boot", "springboot"],
    "React": ["react", "react.js", "reactjs"],
    "Next.js": ["next.js", "nextjs"],
    "Vue.js": ["vue.js", "vuejs", "vue"],
    "Angular": ["angular", "angular.js", "angularjs"],

    # Data / ML / NLP
    "Machine Learning": ["machine learning", "ml"],
    "Deep Learning": ["deep learning", "dl"],
    "Natural Language Processing": ["natural language processing", "nlp"],
    "Computer Vision": ["computer vision", "cv"],
    "Neural Networks": ["neural networks", "neural network", "ann"],
    "Large Language Models": ["large language models", "llm", "llms", "language models"],
    "PyTorch": ["pytorch", "torch"],
    "TensorFlow": ["tensorflow", "tf"],
    "scikit-learn": ["scikit-learn", "sklearn", "scikit learn"],
    "pandas": ["pandas"],
    "NumPy": ["numpy"],
    "Data Analysis": ["data analysis", "data analytics"],
    "Data Visualization": ["data visualization", "data viz"],
    "Statistics": ["statistics", "statistical analysis"],
    "Power BI": ["power bi", "powerbi"],
    "Tableau": ["tableau"],

    # Databases
    "PostgreSQL": ["postgresql", "postgres"],
    "MySQL": ["mysql"],
    "MongoDB": ["mongodb", "mongo"],
    "Redis": ["redis"],
    "SQLite": ["sqlite"],

    # Infra / DevOps
    "Docker": ["docker", "containerization"],
    "Kubernetes": ["kubernetes", "k8s"],
    "AWS": ["aws", "amazon web services"],
    "Azure": ["azure", "microsoft azure"],
    "GCP": ["gcp", "google cloud", "google cloud platform"],
    "CI/CD": ["ci/cd", "ci cd", "continuous integration", "continuous deployment"],
    "Git": ["git", "version control"],
    "Linux": ["linux", "unix"],

    # Other
    "REST APIs": ["rest api", "rest apis", "restful api", "restful apis"],
    "GraphQL": ["graphql"],
    "Microservices": ["microservices", "microservice architecture"],
    "Agile": ["agile", "scrum"],
    "System Design": ["system design"],
    "Testing": ["unit testing", "test automation", "pytest", "junit"],
}

# Flat lookup: alias (lowercased) -> canonical name, built once at import time.
ALIAS_TO_CANONICAL: dict[str, str] = {}
for _canonical, _aliases in SKILLS_TAXONOMY.items():
    ALIAS_TO_CANONICAL[_canonical.lower()] = _canonical
    for _alias in _aliases:
        ALIAS_TO_CANONICAL[_alias.lower()] = _canonical
