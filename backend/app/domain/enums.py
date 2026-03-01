from enum import Enum


class SupportedLanguage(Enum):
    """
    Languages that ACMP can detect and modernize.
    Add new languages here as the platform grows.
    """
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JAVA = "java"


class SupportedFramework(Enum):
    """
    Frameworks that ACMP understands for migration planning.
    UNKNOWN is used when Profiler detects a language but not the framework.
    Add new frameworks here as the platform grows.
    """

    # Python Frameworks
    DJANGO = "django"
    FLASK = "flask"
    FASTAPI = "fastapi"

    # JavaScript / TypeScript Frameworks
    EXPRESS = "express"
    REACT = "react"

    # Java Frameworks
    SPRING = "spring"

    # Fallback — when framework cannot be identified
    UNKNOWN = "unknown"