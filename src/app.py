from flask import Flask, render_template, request, url_for
from src.models.optimisation import deap_evolve, deap_save


app = Flask(__name__)
#app._static_folder = 'src/static/libraries'

@app.route('/')
def home_page():
    return render_template('home.html')


###############################################################################
@app.route('/calculate', methods=['POST', 'GET']) #need to look at which urls point to where and what is returned by each when submit is pressed
def calculate_results():
    loLWL = float(request.form['lo_lwl'])
    loB = float(request.form['lo_b'])
    loT = float(request.form['lo_t'])
    loVolDisp = float(request.form['lo_vol_disp'])
    loCwp = float(request.form['lo_cwp'])
    hiLWL = float(request.form['hi_lwl'])
    hiB = float(request.form['hi_b'])
    hiT = float(request.form['hi_t'])
    hiVolDisp = float(request.form['hi_vol_disp'])
    hiCwp = float(request.form['hi_cwp'])
    popsize = int(request.form['pop_size'])
    maxgen = int(request.form['max_gen'])

    record, logbook, resFitAll, stabFitAll, LWLAll, BeamAll, DraftAll, DispAll, CwpAll, number_of_runs = deap_evolve(loLWL, loB, loT, loVolDisp, loCwp, hiLWL, hiB, hiT, hiVolDisp, hiCwp, popsize, maxgen)
    deap_save(resFitAll, stabFitAll, LWLAll, BeamAll, DraftAll, DispAll, CwpAll, number_of_runs)
    return render_template("results.html")
################################################################################

if __name__ == '__main__':
    app.run(debug=True)