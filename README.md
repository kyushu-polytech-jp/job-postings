# job-postings

Firebase Hosting project for Poly9Wanted

## Hosting targets
- poly9wanted
- poly9mente

## Local tools
- Firebase CLI
- Python 3.x (for maintenance CGI)

## Deploy
firebase deploy --only hosting:poly9wanted
firebase deploy --only hosting:poly9mente

## Local Web cgi http://10.33.1.100/poly9-bin/mente.py
## /var/www/cgi-bin/mente.py
- src/python/mente.py

