from flask import Flask, render_template, request, jsonify, send_from_directory
from datetime import datetime
import pytz
from BusTrafficService import Tracking

app = Flask(__name__)

# Глобальні змінні для зберігання статистики
total_requests = 0
total_visitors = 0
last_activity = None

# Часовий пояс Києва
kiev_timezone = pytz.timezone("Europe/Kiev")

tracking = Tracking()

@app.route('/')
def home():
    global total_visitors
    total_visitors += 1
    return render_template('index.html', total_requests=total_requests, total_visitors=total_visitors, last_activity=last_activity)

@app.route('/bus_stops', methods=['GET'])
def bus_stops():
    # Повертаємо список зупинок
    stops = list(tracking.bus_arrival_times.keys())
    return jsonify(stops)

@app.route('/schedule', methods=['GET'])
def schedule():
    global total_requests
    bus_stop = request.args.get('bus_stop_name')
    offset = request.args.get('offset', 0)
    if not bus_stop:
        return jsonify({"error": "Для відображення інформації, будь ласка оберіть зупинку із списку"}), 400
    try:
        tracking.offset = int(offset)
        result = tracking.get_bus_schedule(bus_stop)
        if "stops" in result:
            return jsonify(result)
        total_requests += 1
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": f"Помилка: {e}"}), 500

@app.route('/full_schedule', methods=['GET'])
def full_schedule():
    global total_requests
    bus_stop = request.args.get('bus_stop_name')
    offset = request.args.get('offset', 0)
    if not bus_stop:
        return jsonify({"error": "Для відображення інформації, будь ласка оберіть зупинку із списку"}), 400
    try:
        tracking.offset = int(offset)
        result = tracking.get_bus_schedule(bus_stop)
        if "stops" in result:
            return jsonify(result)
        total_requests += 1
        return jsonify({
            "bus_stop": result["bus_stop"],
            "full_schedule": result["full_schedule"]
        })
    except Exception as e:
        return jsonify({"error": f"Помилка: {e}"}), 500

@app.route('/update_last_activity', methods=['POST'])
def update_last_activity():
    global last_activity
    last_activity = datetime.now(kiev_timezone).strftime('%H:%M')
    return jsonify({"last_activity": last_activity})

@app.route('/statistics', methods=['GET'])
def statistics():
    global total_requests, total_visitors, last_activity
    return jsonify({
        "total_visitors": total_visitors,
        "total_requests": total_requests,
        "last_activity": last_activity
    })

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/telegram')
def telegram():
    return render_template('telegram.html')

@app.route('/viber')
def viber():
    return render_template('viber.html')

@app.route('/api')
def api():
    return render_template('api.html')

@app.route('/contacts')
def contacts():
    return render_template('contacts.html')

@app.route('/sitemap.xml')
def sitemap():
    return send_from_directory(app.root_path, 'sitemap.xml')

@app.route('/robots.txt')
def robots():
    return send_from_directory(app.root_path, 'robots.txt')

if __name__ == "__main__":
    from werkzeug.serving import run_simple
    run_simple('0.0.0.0', 5005, app)
