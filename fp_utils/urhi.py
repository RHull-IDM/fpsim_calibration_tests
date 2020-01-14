import os
import itertools
import numpy as np
from multiprocessing import Pool
from pathlib import Path
import pandas as pd

from fp_utils.base import Base

class URHI(Base):

    yeardict = {
        'Baseline':    os.path.join('Baseline', 'SEN_base_wm_20160427.dta'),
        'Midline':     os.path.join('Midline', 'SEN_mid_wm_match_20160609.dta'),
        'Endline':     os.path.join('Endline', 'SEN_end_wm_match_20160505.dta'),
    }

    indicators = {
        'Baseline': {'line':'Line', 'hhnum': 'HHNUM', 'iyear':'Year', 'imon':'Month', 'w102':'Age', 'w208':'Parity', 'method':'Method', 'methodtype':'MethodType', 'wm_allcity_wt':'Weight', 'city':'City', 'unmet_cmw': 'Unmet'},
        'Midline': {'line':'Line', 'hhnum': 'HHNUM', 'mwiyear':'Year', 'mwimon':'Month', 'mw102':'Age', 'mw208b':'Parity', 'mmethod':'Method', 'mmethodtype':'MethodType', 'mwm_allcity_wt':'Weight', 'mcity':'City', 'munmet_cmw': 'Unmet'},
        'Endline': {'line':'Line', 'hhnum': 'HHNUM', 'ewiyear':'Year', 'ewimon':'Month', 'ew102':'Age', 'ew208':'Parity', 'emethod':'Method', 'emethodtype':'MethodType', 'ewoman_weight_6city':'Weight', 'ecity':'City', 'eunmet_cmw': 'Unmet'},
    }

    def __init__(self, foldername, force_read=False, cores=8):
        self.cachefn = os.path.join('cache', 'urhi.hdf')
        self.results_dir = os.path.join('results', 'URHI')

        super().__init__(foldername, force_read, cores)

        self.cache_read()
        self._clean()

        surveyname_to_date = self.data.groupby('SurveyName')[['Year', 'Month']].mean().apply(lambda x: x['Year'] + x['Month']/12, axis=1)
        surveyname_to_date.name = 'Date'
        self.data = pd.merge(self.data, surveyname_to_date, on='SurveyName')

        self.create_bins()
        self.data['Survey'] = 'URHI'


    def cache_read(self):
        # Read in the URHI data, from file if necessary or requested
        if self.force_read:
            self.data = self.read()
        else:
            try:
                store = pd.HDFStore(self.cachefn)
                self.data = store['data'] #pd.read_hdf(cachefn, key='data')
                store.close()
            except:
                store.close()
                self.data = self.read()


    def load(self, x):
        year, path = x
        filename = os.path.join(self.foldername, path)
        print(f'Loading {year} from file {filename}')

        fn = Path(filename).resolve().stem
        print(f'File: {filename} ...')
        data = pd.read_stata(filename, convert_categoricals=False)

        data['SurveyName'] = year
        found_keys = []
        for k in self.indicators[year].keys():
            if k not in data.columns:
                print(f'SurveyName {year} is missing {k}')
            else:
                found_keys.append(k)


        data = data[['SurveyName'] + found_keys]

        values = pd.io.stata.StataReader(filename).value_labels()
        replace_dict = {k: values[k.upper()] if k.upper() in values else values[k] for k in found_keys if k in values or k.upper() in values}

        # Ugh
        if year == 'Midline':
            replace_dict['mmethodtype'] = values['methodtype'] # Doesn't appear to be an entry for mmethodtype?
        elif year == 'Endline':
            replace_dict['emethod'] = values['method'] # Doesn't appear to be an entry for emethod?
            replace_dict['emethodtype'] = values['methodtype'] # Doesn't appear to be an entry for emethodtype?

        for k in replace_dict.keys():
            if self.indicators[year][k] == 'Parity':
                print('Skipping parity')
                continue

            if 0 in replace_dict[k]:
                # zero-based
                data[k] = data[k].fillna(-1)
            else:
                # assume one-based
                data[k] = data[k].fillna(0) - 1

            try:
                data[k] = pd.Categorical.from_codes(data[k], categories = [unidecode.unidecode(v[1]) for v in sorted(replace_dict[k].items(), key = lambda x: x[0])] )
            except:
                print('Difficulty:', year, k, data[k].unique(), replace_dict[k])
                data[k] = data[k].replace(replace_dict[k]).map(str) #.astype('category')
                print(data[k])

        data.rename(columns=self.indicators[year], inplace=True)

        age_edges = list(range(15,55,5)) + [99]
        a,b = itertools.tee(age_edges)
        a = list(a)[:-1]
        next(b)
        labels = [f'{c}-{d}' for c,d in zip(a,b)]
        data['AgeBin'] = pd.cut(data['Age'], bins = age_edges, labels=labels, right=False)

        parity_edges = list(range(6+1)) + [99]
        a,b = itertools.tee(parity_edges)
        a = list(a)[:-1]
        next(b)
        labels = [f'{c}-{d}' for c,d in zip(a,b)]
        data['ParityBin'] = pd.cut(data['Parity'], bins = parity_edges, labels=labels, right=False)

        if True:
            values = pd.io.stata.StataReader(filename).value_labels()
            codebook = pd.io.stata.StataReader(filename).variable_labels()

            pd.DataFrame({'keys': list(codebook.keys()), 'values': list(codebook.values())}).set_index('keys').to_csv(f'codebook_{fn}.csv')

        return data


    def read(self):
        with Pool(self.cores) as p:
            data_list = p.map(self.load, self.yeardict.items())

        data = pd.concat(data_list)
        data['UID'] = data.apply(lambda x: str(x['HHNUM']) + ' ' + str(x['Line']), axis=1)
        data.set_index('UID', inplace=True)

        data.drop(['HHNUM', 'Line'], axis=1, inplace=True)

        data.to_hdf(self.cachefn, key='data', format='t')

        return data


    def _clean(self):
        self.raw = self.data

        # Parity is all [NaN or 0] at Midline?!  Causes seaborn ploting problems, so fill -1.
        self.data.loc[self.data['SurveyName']=='Midline', 'Parity'] = \
            self.data.loc[self.data['SurveyName']=='Midline', 'Parity'].fillna(0)

        NO_METHOD = 'No method'
        SHORT = 'Short-term'
        LONG = 'Long-term'
        INJECTION = 'Injection'
        OTHER = 'Other'

        self.data.loc[:,'MethodDurability'] = self.data['Method']

        print(self.data.head())

        self.data.replace(
            {
                'Method': {
                    #'Female sterilization': '',
                    #'No method': '',
                    #'Daily pill': '',

                    'Injectables': 'Injectable',
                    'Breastfeeding/LAM': 'LAM',
                    'iucd': 'IUD',
                    'Female condom': 'Condom',
                    'Male condom': 'Condom',
                    'Implants': 'Implant',

                    'Natural methods': 'Traditional',
                    'Other traditional method': 'Traditional',

                    'sdm': 'Other modern',
                    'Other modern method': 'Other modern',
                    'Emergency pill': 'Other modern',
                },

                'MethodDurability': {
                    #'No method': NO_METHOD, # Causes...  "ValueError: Replacement not allowed with overlapping keys and values"

                    'Daily pill': SHORT,
                    'Female condom': SHORT,
                    'Male condom': SHORT,

                    'Injectables': INJECTION,

                    'Female sterilization': LONG,
                    'iucd': LONG,
                    'Implants': LONG,

                    'Natural methods': OTHER,
                    'Breastfeeding/LAM': OTHER,
                    'Other traditional method': OTHER,
                    'sdm': OTHER,
                    'Other modern method': OTHER,
                    'Emergency pill': OTHER,
                },

                'Unmet': {
                    '-1.0': 'Unknown',
                    'No unmet need': 'No',
                    'Unmet need': 'Yes',
                    'Missing': 'Unknown',
                }
            },
            inplace=True
        )

        self.data.reset_index(inplace=True)
