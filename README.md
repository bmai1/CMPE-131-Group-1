Clone this repo: `git clone https://github.com/bmai1/CMPE-131-Group-1.git`

Remember to git pull to update local code before working on stuff.
Push to your branch and make a pull request and I'll review it.

Usage: 
```
python -m venv env
. env/bin/activate
pip install -r requirements.txt
flask run
```
(if venv already created, skip the first and third command)

Run `python init.py` if creating or updating a database (users.db).

Flask defaults to [127.0.0.1:5000](http://127.0.0.1:5000).

Important: manually create a file named `.env` in the same folder as `app.py`. Then copy and paste the key I posted in Discord. Otherwise the session key won't load and you can't login.

Try username: bobross password: 12345 instead of creating new accounts to avoid merge conflicts with database.
