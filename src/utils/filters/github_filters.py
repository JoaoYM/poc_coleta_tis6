def is_human(author_login: str) -> bool:
    """Filtra bots via sufixo padrão e uma blacklist de ofensores conhecidos."""
    if not author_login:
        return False
        
    login_lower = author_login.lower()
    if login_lower.endswith('[bot]'):
        return False
        
    known_bots = {
        "dependabot", "dependabot-preview", "renovate", "snyk-bot", 
        "github-actions", "coveralls", "codecov", "greenkeeper", 
        "netlify", "vercel", "sonarcloud", "travis-ci"
    }
    return login_lower not in known_bots