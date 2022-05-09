'''
Class to define and run scenarios
'''

import numpy as np
import pandas as pd
import sciris as sc
import fpsim as fp
import fp_analyses as fa
from . import utils as fpu
from . import interventions as fpi

__all__ = ['Scenarios','update_methods']


# Define basic things here
default_pars = fa.senegal_parameters.make_pars()
method_names = default_pars['methods']['names']


def get_pars(location=None):
    ''' Temporary function for getting parameters '''
    if not location:
        pars = default_pars
    elif location == 'senegal':
        pars = fa.senegal_parameters.make_pars()
    else:
        errormsg = f'Location "{location}" is not currently supported'
        raise NotImplementedError(errormsg)
    return sc.dcp(pars)



class Scenarios(sc.prettyobj):
    '''
    Run different intervention scenarios
    '''

    def __init__(self, pars=None, repeats=None, scen_year=None, scens=None, location=None):
        self.pars = pars
        self.repeats = repeats
        self.scen_year = scen_year
        self.scens = sc.tolist(scens)
        self.location = location
        self.simslist = []
        self.msim = None
        self.msims = []
        return


    def add_scen(self, scen=None, label=None):
        ''' Add a scenario or scenarios to the Scenarios object '''
        scens = sc.tolist(scen)
        if label:
            for scen in scens:
                scen['label'] = label
        self.scens += scens
        return


    def make_sims(self, label=None, **kwargs):
        ''' Create a list of sims that are all identical except for the random seed '''
        sims = sc.autolist()
        for i in range(self.repeats):
            pars = sc.mergedicts(get_pars(self.location), self.pars, _copy=True)
            pars.setdefault('seed', 0)
            pars.update(kwargs)
            pars['seed'] += i
            sims += fp.Sim(pars=pars, label=label)
        return sims


    def make_scens(self):
        ''' Convert a scenario specification into a list of sims '''
        for scen in self.scens:
            interventions = sc.autolist()
            for entry in sc.tolist(scen):
                year = entry.pop('scen_year', self.scen_year)
                matrix = entry.pop('matrix', None)
                label = entry.pop('label', None)
                if year is None:
                    errormsg = 'Scenario year must be specified in either the scenario entry or the Scenarios object'
                    raise ValueError(errormsg)
                interventions += fp.update_methods(scen=entry, year=year, matrix=matrix)
            sims = self.make_sims(interventions=interventions, label=label)
            self.simslist.append(sims)
        return


    def run(self, *args, **kwargs):
        ''' Actually run a list of sims '''

        # Check that it's set up
        if not self.scens:
            errormsg = 'No scenarios are defined'
            raise ValueError(errormsg)
        if not self.simslist:
            self.make_scens()

        # Create msim
        msims = sc.autolist()
        for sims in self.simslist:
            msims += fp.MultiSim(sims)
        self.msim = fp.MultiSim.merge(*msims)

        # Run
        self.msim.run(**kwargs)

        # Process
        self.msim_merged =self.msim.remerge()
        self.analyze_sims()
        return


    def plot_sims(self, **kwargs):
        return self.msim.plot(plot_sims=False, **kwargs)


    def plot_scens(self, **kwargs):
        return self.msim_merged.plot(plot_sims=True, **kwargs)


    def analyze_sims(self, start, end):
        ''' Take a list of sims that have different labels and count the births in each '''

        def count_births(sim):
            year = sim.results['t']
            births = sim.results['births']
            inds = sc.findinds((year >= start), year < end)
            output = births[inds].sum()
            return output

        def method_failure(sim):
            year = sim.results['tfr_years']
            meth_fail = sim.results['method_failures_over_year']
            inds = sc.findinds((year >= start), year < end)
            output = meth_fail[inds].sum()
            return output

        def count_pop(sim):
            year = sim.results['tfr_years']
            popsize = sim.results['pop_size']
            inds = sc.findinds((year >= start), year < end)
            output = popsize[inds].sum()
            return output

        def mean_tfr(sim):
            year = sim.results['tfr_years']
            rates = sim.results['tfr_rates']
            inds = sc.findinds((year >= start), year < end)
            output = rates[inds].mean()
            return output

        # Split the sims up by scenario
        results = sc.objdict()
        results.sims = sc.objdict(defaultdict=sc.autolist)
        for sim in self.msim.sims:
            results.sims[sim.label] += sim

        # Count the births across the scenarios
        raw = sc.objdict(defaultdict=sc.autolist)
        for key,sims in results.sims.items():
            for sim in sims:
                n_births = count_births(sim)
                n_fails  = method_failure(sim)
                n_pop = count_pop(sim)
                n_tfr = mean_tfr(sim)
                raw.scenario += key      # Append scenario key
                raw.births   += n_births # Append births
                raw.fails    += n_fails  # Append failures
                raw.popsize  += n_pop    # Append population size
                raw.tfr      += n_tfr    # Append mean tfr rates

        # Calculate basic stats
        results.stats = sc.objdict()
        for statkey in ['mean', 'median', 'std', 'min', 'max']:
            results.stats[statkey] = sc.objdict()
            for k,vals in raw.items():
                if k != 'scenario':
                    results.stats[statkey][k] = getattr(np, statkey)(vals)

        # Also save as pandas
        results.df = pd.DataFrame(raw)
        self.results = results

        return


def key2ind(sim, key):
    """
    Take a method key and convert to an int, e.g. 'Condoms' → 7
    """
    ind = key
    if ind in [None, 'all']:
        ind = slice(None) # This is equivalent to ":" in matrix[:,:]
    elif isinstance(ind, str):
        ind = sim.pars['methods']['map'][key]
    return ind


def getval(v):
    ''' Handle different ways of supplying a value -- number, distribution, function '''
    if sc.isnumber(v):
        return v
    elif isinstance(v, dict):
        return fpu.sample(**v)[0]
    elif callable(v):
        return v()


class update_methods(fpi.Intervention):
    """
    Intervention to modify method efficacy and/or switching matrix.

    Args:
        year (float): The year we want to change the method.
        scen (dict): Define the scenario to run:

            probs (list): A list of dictionaries where each dictionary has the following keys:

                source (str): The source method to be changed.
                dest (str) The destination method to be changed.
                factor (float): The factor by which to multiply existing probability; OR
                value (float): The value to replace the switching probability value.
                keys (list): A list of strings representing age groups to affect.

            eff (dict):
                An optional key for changing efficacy; its value is a dictionary with the following schema:

                    {method: efficacy}
                        Where method is the method to be changed, and efficacy is the new efficacy (can include multiple keys).

        matrix (str): One of ['probs_matrix', 'probs_matrix_1', 'probs_matrix_1-6'] where:

            probs_matrix:
                Changes the specified uptake at the corresponding year regardless of state.
            probs_matrix_1
                Changes the specified uptake for all individuals in their first month postpartum.
            probs_matrix_1-6
                Changes the specified uptake for all individuals that are in the first 6 months postpartum.
    """

    def __init__(self, year, scen, matrix=None):
        """
        Initializes self.year/scen/matrix from parameters
        """
        super().__init__()
        self.year   = year
        self.scen   = scen
        self.matrix = matrix if matrix else 'probs_matrix'
        valid_matrices = ['probs_matrix', 'probs_matrix_1', 'probs_matrix_1-6'] # TODO: be less subtle about the difference between normal and postpartum matrices
        if self.matrix not in valid_matrices:
            raise sc.KeyNotFoundError(f'Matrix must be one of {valid_matrices}, not "{matrix}"')
        return


    def apply(self, sim, verbose=True):
        """
        Applies the efficacy or contraceptive uptake changes if it is the specified year
        based on scenario specifications.
        """

        if sim.y >= self.year and not(hasattr(sim, 'modified')):
            sim.modified = True

            # Implement efficacy
            if 'eff' in self.scen:
                for k,rawval in self.scen.eff.items():
                    v = getval(rawval)
                    ind = key2ind(sim, k)
                    orig = sim.pars['method_efficacy'][ind]
                    sim.pars['method_efficacy'][ind] = v
                    if verbose:
                        print(f'At time {sim.y:0.1f}, efficacy for method {k} was changed from {orig:0.3f} to {v:0.3f}')

            # Implement method mix shift
            if 'probs' in self.scen:
                for entry in self.scen.probs:
                    source = key2ind(sim, entry['source'])
                    dest   = key2ind(sim, entry['dest'])
                    factor = entry.pop('factor', None)
                    value  = entry.pop('value', None)
                    keys   = entry.pop('keys', None)
                    if keys is None:
                        keys = sim.pars['methods']['probs_matrix'].keys()

                    for k in keys:
                        if self.matrix == 'probs_matrix':
                            matrices = sim.pars['methods']
                        else:
                            matrices = sim.pars['methods_postpartum']
                        matrix = matrices[self.matrix][k]
                        orig = matrix[source, dest]
                        if factor is not None:
                            matrix[source, dest] *= getval(factor)
                        elif value is not None:
                            matrix[source, dest] = getval(value)
                        if verbose:
                            print(f'At time {sim.y:0.1f}, matrix for age group {k} was changed from:\n{orig}\nto\n{matrix[source, dest]}')


        return