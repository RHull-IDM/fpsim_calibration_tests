'''
Optimize for birth spacing parameters
'''

import sciris as sc
import numpy as np
import pylab as pl
import fpsim as fp

# Define best, low, high limits for the parameters
calib_pars = dict(
    space0_6   = [0.5, 0.2, 1.5],
    space9_15  = [0.5, 0.2, 1.5],
    space18_24 = [2.0, 0.5, 3.0],
    space27_36 = [1.0, 0.5, 3.0],
)

spacing_file = 'BirthSpacing.obj'

spacing_bins = sc.odict({'0-12': 0, '12-24': 1, '24-48': 2, '>48': 4})  # Spacing bins in years; CK: need to check that this is right
min_age = 15
max_age = 50

# Load birth spacing data
data = sc.load(spacing_file)


class SpacingCalib(fp.Calibration):
    ''' Custom version of calibration, just for birth spacing '''
    
    def __init__(self, calib_pars, verbose=True, keep_db=False, **kwargs):
        
        # Settings
        self.calib_pars = calib_pars
        self.verbose    = verbose
        self.keep_db    = keep_db
        
        # Configure Optuna
        self.set_optuna_defaults()
        self.configure_optuna(**kwargs)
        return


    def validate_pars(self):
        ''' Redefine this to skip it '''
        pass


    def make_sim(self, spacing_pars):
        base_pars = dict(location='senegal', n_agents=1000, verbose=0)
        sim = fp.Sim(base_pars)
        sim.pars['spacing_pref']['preference'][:3]  = spacing_pars['space0_6']
        sim.pars['spacing_pref']['preference'][3:6] = spacing_pars['space9_15']
        sim.pars['spacing_pref']['preference'][6:9] = spacing_pars['space18_24']
        sim.pars['spacing_pref']['preference'][9:]  = spacing_pars['space27_36']
        return sim
    
    
    def get_data_spaces(self, data):
        # Extract birth spacing data from  data
        spacing = data['spacing']  # Extract from data
        data_spacing_counts = sc.odict().make(keys=spacing_bins.keys(), vals=0.0)
    
        # Spacing bins from data
        spacing_bins_array = sc.cat(spacing_bins[:], np.inf)
        for i in range(len(spacing_bins_array) - 1):
            lower = spacing_bins_array[i]
            upper = spacing_bins_array[i + 1]
            matches = np.intersect1d(sc.findinds(spacing >= lower), sc.findinds(spacing < upper))
            data_spacing_counts[i] += len(matches)
    
        data_spacing_counts[:] /= data_spacing_counts[:].sum()
        spaces = np.array(data_spacing_counts.values())
        return spaces
    
    
    def get_spaces(self, sim):
        model_spacing_counts = sc.odict().make(keys=spacing_bins.keys(), vals=0.0)
        ppl = sim.people
        for i in range(len(ppl)):
            if ppl.alive[i] and not ppl.sex[i] and ppl.age[i] >= min_age and ppl.age[i] < max_age:
                if len(ppl.dobs[i]) > 1:
                    for d in range(len(ppl.dobs[i]) - 1):
                        space = ppl.dobs[i][d + 1] - ppl.dobs[i][d]
                        ind = sc.findinds(space > spacing_bins[:])[-1]
                        model_spacing_counts[ind] += 1
    
        model_spacing_counts[:] /= model_spacing_counts[:].sum()
        spaces = np.array(model_spacing_counts.values())
        return spaces
    
    
    def compute_mismatch(self, data_spaces, sim_spaces):
        diffs = np.array(data_spaces) - np.array(sim_spaces)
        mismatch = sum(diffs ** 2)
        return mismatch

    
    def run_exp(self, pars, label=None, return_exp=False):
        sim = self.make_sim(pars)
        sim.label = label
        sim.run()
        sim.sim_spaces = self.get_spaces(sim)
        sim.data_spaces = self.get_data_spaces(data)
        sim.mismatch = self.compute_mismatch(sim.data_spaces, sim.sim_spaces)
        if return_exp:
            return sim
        else:
            return sim.mismatch
    
    
    def run_trial(self, trial):
        spacing_pars = dict()
        for key, (vbest, vmin, vmax) in self.calib_pars.items():
            spacing_pars[key] = trial.suggest_float(key, vmin, vmax)
        mismatch = self.run_exp(spacing_pars)
        return mismatch

    
    def plot_spacing(self):
        pl.figure(figsize=(12,6))
        
        for i,sim in enumerate([self.before, self.after]):
            data = sim.data_spaces
            model = sim.sim_spaces
            pl.subplot(1,2,i+1)
            nbars = len(data)
            y = np.arange(nbars)
            dy = 0.2
            kw = dict(height=0.2)
            pl.barh(y+dy, data, label='Data', facecolor='k', **kw)
            pl.barh(y, model, label='Model', facecolor='cornflowerblue', **kw)
            pl.barh(y-dy, data - model, label='Diff', facecolor='red', **kw)
            pl.yticks(y, spacing_bins.keys())
            pl.title(f'{sim.label}\n(mismatch: {sim.mismatch*1000:n})')
            pl.legend()
        
        return
        


if __name__ == '__main__':
    
    trials = 200
    
    with sc.timer():
        calib = SpacingCalib(calib_pars, total_trials=trials)
        calib.calibrate()
        calib.plot_spacing()
        sc.pp(calib.to_json()[:5])
