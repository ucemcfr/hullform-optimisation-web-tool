from flask import Flask, render_template, request, url_for
from src.models.optimisation import deap_evolve, deap_save
from src.database import Database
from src.models.Ship import Ship

app = Flask(__name__)
#app._static_folder = 'src/static/libraries'

Database.initialize()

@app.route('/')
def home_page():
    return render_template('home.html')

@app.route('/ships/new', methods=['POST', 'GET'])
def save_ship():
    if request.method == 'GET':
        return render_template('save_ship.html') # this says that if you just type in the URL you get returned the html file

    else: # this happens when the submit button is pressed because the method specified in the associated div in save_ship.html is "post"

        lwl = float(request.form['lwl'])
        loa = float(request.form['loa'])
        bwl = float(request.form['bwl'])
        boa = float(request.form['boa'])
        draft = float(request.form['draft'])

        vol_disp = float(request.form['vol_disp'])
        lcb = float(request.form['lcb'])
        vcb = float(request.form['vcb']) # this is distance below waterline
        velocity = float(request.form['velocity'])
        c_m = float(request.form['c_m'])
        c_wp = float(request.form['c_wp'])
        heading = float(request.form['heading'])

        total_resistance = float(request.form['total_resistance']) # TODO set an if statement for these three that if they are None they are set to None, this may not be needed?
        k_m = float(request.form['k_m'])
        max_vert_acceleration = float(request.form['max_vert_acceleration'])

        new_ship = Ship(velocity, lwl, loa, bwl, boa, draft, vol_disp, lcb, c_m, c_wp, heading, vcb, total_resistance, k_m, max_vert_acceleration)
        new_ship.save_to_mongo()

        return render_template('home.html') #TODO return list of database entries when submitted.

# something like....
@app.route('/ships/filter', methods=['POST', 'GET'])
def filter_ships():
    if request.method == 'GET':
        return render_template('filter_ships.html') # this says that if you just type in the URL you get returned the html file

    else:
        query = {}

        if request.form['low_lwl'] is not None:
            low_lwl = float(request.form['low_lwl'])
            query['lwl']= {'$gt': low_lwl}

        if request.form['high_lwl'] is not None:
            high_lwl = float(request.form['high_lwl'])
            #if query['lwl'] is None:
            #        query['lwl'] = {}
            query['lwl']['$lt'] = high_lwl

        if request.form['low_loa'] is not None:
            low_loa = float(request.form['low_loa'])
            query['loa'] = {'$gt': low_loa}

        if request.form['high_loa'] is not None:
            high_loa = float(request.form['high_loa'])
            query['loa']['$lt'] = high_loa

        if request.form['low_bwl'] is not None:
            low_bwl = float(request.form['low_bwl'])
            query['bwl'] = {'$gt': low_bwl}

        if request.form['high_bwl'] is not None:
            high_bwl = float(request.form['high_bwl'])
            query['bwl']['$lt'] = high_bwl

        print(query)
        mycollection = 'previous_designs'
        results_cursor = Database.find(mycollection, query)

        for x in results_cursor:
            print(x)

        return render_template('home.html')

###############################################################################
# @app.route('/calculate', methods=['POST', 'GET']) #need to look at which urls point to where and what is returned by each when submit is pressed
# def calculate_results():
#     loLWL = float(request.form['lo_lwl'])
#     loB = float(request.form['lo_b'])
#     loT = float(request.form['lo_t'])
#     loVolDisp = float(request.form['lo_vol_disp'])
#     loCwp = float(request.form['lo_cwp'])
#     hiLWL = float(request.form['hi_lwl'])
#     hiB = float(request.form['hi_b'])
#     hiT = float(request.form['hi_t'])
#     hiVolDisp = float(request.form['hi_vol_disp'])
#     hiCwp = float(request.form['hi_cwp'])
#     popsize = int(request.form['pop_size'])
#     maxgen = int(request.form['max_gen'])
#
#     record, logbook, resFitAll, stabFitAll, LWLAll, BeamAll, DraftAll, DispAll, CwpAll, number_of_runs = deap_evolve(loLWL, loB, loT, loVolDisp, loCwp, hiLWL, hiB, hiT, hiVolDisp, hiCwp, popsize, maxgen)
#     deap_save(resFitAll, stabFitAll, LWLAll, BeamAll, DraftAll, DispAll, CwpAll, number_of_runs)
#     return render_template("results.html")
################################################################################

if __name__ == '__main__':
    app.run(debug=True)




#
#   {keyname $lt: form value} --> check syntax of this.

# for result in results_cursor:
# print(result)
