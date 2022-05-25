import threading
import requests
from datetime import datetime, timedelta
from flask import render_template, Flask, request, url_for, flash, redirect
import os


app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24).hex()

# Starting with no tasks
messages = [{'title': 'Service is not ready',
             'content': 'Go to settings page and fill the form'}]


# For root path render default template with current tasks
@app.route("/")
def index():
    return render_template('index.html', messages=messages)


def check_date(r_f):
    """"
    This function checks the current date
    If 3 days after today is an official holiday - creates task in bitrix 24
    :params r_f: request form from page /settings with all information about created task
    """
    # Unpacking all information
    DOMAIN = r_f['domain']
    HOOK_KEY = r_f['hook_key']
    TITLE = r_f['title']
    RESPONSIBLE_ID = r_f['responsible_id']
    DESCRIPTION = r_f['description']

    # Get date 3 days after today
    YYYY, MM, DD = [int(i) for i in (datetime.today().date() + timedelta(days=3)).__str__().split("-")]
    # Checks if it is a holiday
    resp = requests.get(
        f"https://htmlweb.ru/service/api.php?holiday&type=1&d_from={YYYY}-{MM}-{DD}&d_to={YYYY}-{MM}-{DD}")
    if "За выбранный период нет данных" in resp.text:
        print("No data")
    else:
        # Create task in bitrix 24 with webhook (must be prepared before app running!)
        web_hook = "".join([f"https://{DOMAIN}.bitrix24.ru/rest",
                            f"/{RESPONSIBLE_ID}",
                            f"/{HOOK_KEY}",
                            f"/task.item.add.json?",
                            f"fields[TITLE]={TITLE}&",
                            f"fields[RESPONSIBLE_ID]={RESPONSIBLE_ID}&",
                            f"fields[DESCRIPTION]={DESCRIPTION}"])
        response = requests.post(web_hook)
        print("Задача создана..." if response.ok else "Возникла ошибка вебхука...")


# Settings page
@app.route('/settings/', methods=('GET', 'POST'))
def settings():
    if request.method == 'POST':
        # Creates daemon, that checks date every day
        check_date_thread = threading.Thread(target=check_date, name="Task daemon", args=[request.form])
        check_date_thread.start()

        if None in request.form.values():
            # Check if form is filled with values
            flash('Fill all fields!')
        else:
            # Can create multiple tasks
            messages.append({'title': 'Service is running',
                             'content': f'{request.form["title"]} task will appear 3 days before official holiday'})
            if messages[0]["title"] == "Service is not ready":
                _ = messages.pop(0)
            return redirect(url_for('index'))

    return render_template('settings.html')


app.run(host="0.0.0.0", port=5005)
