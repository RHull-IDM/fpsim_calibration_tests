'''
A script for running plotting to compare the model to data
'''

import numpy as np
import pandas as pd
import sciris as sc
import fpsim as fp
import pylab as pl
import seaborn as sns

# Global Variables

# Name of the country being calibrated. To note that this should match the name of the country data folder
country = 'ethiopia'

sc.tic()

# Set options for plotting
do_plot_sim = True
do_plot_asfr = True
do_plot_methods = True
do_plot_skyscrapers = True
do_plot_cpr = True
do_plot_tfr = True
do_plot_pop_growth = True
do_plot_birth_space_afb = True

# Set option to save figures
do_save = 1


# Set up global variables
age_bin_map = {
        '10-14': [10, 15],
        '15-19': [15, 20],
        '20-24': [20, 25],
        '25-29': [25, 30],
        '30-34': [30, 35],
        '35-39': [35, 40],
        '40-44': [40, 45],
        '45-49': [45, 50]
}

min_age = 15
max_age = 50
first_birth_age = 25  # age to start assessing first birth age in model
bin_size = 5
mpy = 12 # months per year


# Import country data files to compare
skyscrapers = pd.read_csv(f'./{country}/{country}_skyscrapers.csv') # Age-parity distribution file
use = pd.read_csv(f'./{country}/use_{country}.csv') #Dichotomous contraceptive method use
data_spaces = pd.read_csv(f'./{country}/birth_spacing_dhs.csv')  # Birth-to-birth interval data
data_afb = pd.read_csv(f'./{country}/afb.table.csv')  # Ages at first birth in DHS for women age 25-50
data_cpr = pd.read_csv(f'./{country}/{country}_cpr.csv')  # From UN Data Portal
data_asfr = pd.read_csv(f'./{country}/{country}_asfr.csv')
data_methods = pd.read_csv(f'./{country}/mix_{country}.csv')
data_tfr = pd.read_csv(f'./{country}/{country}_tfr.csv')
data_popsize = pd.read_csv(f'./{country}/{country}_popsize.csv')

# Set up sim for country
pars = fp.pars(location=country)
pars['n_agents'] = 100_000 # Small population size
pars['end_year'] = 2020 # 1961 - 2020 is the normal date range

# Free parameters for calibration
pars['fecundity_var_low'] = 0.95
pars['fecundity_var_high'] = 1.05
pars['exposure_factor'] = 1
pars['high_parity'] = 1
pars['high_parity_nonuse'] = 1

# Last free parameter, postpartum sexual activity correction or 'birth spacing preferece'
# Set all to 1 to reset
spacing_pars = {'space0_6': 1, 'space18_24': 1, 'space27_36': 1, 'space9_15': 1}  # output from 'optimize-space-prefs-kenya.py'
pars['spacing_pref']['preference'][:3] = spacing_pars['space0_6']
pars['spacing_pref']['preference'][3:6] = spacing_pars['space9_15']
pars['spacing_pref']['preference'][6:9] = spacing_pars['space18_24']
#pars['spacing_pref']['preference'][9:] = spacing_pars['space27_36'] # Removing this bin for Kenya as it doesn't extend out

# Only other free parameters are age-based exposure and parity-based exposure, can adjust manually in {country}.py

sim = fp.Sim(pars=pars)
sim.run()

# Plot results from sum run
if do_plot_sim:
    sim.plot()

# Save results
res = sim.results

# Save people from sim
ppl = sim.people

# Set up dictionaries to compare from model vs data
data_dict = {}
model_dict = {} # For comparison from model to data


def pop_growth_rate(years, population):
        '''
        Calculates growth rate as a time series to help compare model to data
        '''
        growth_rate = np.zeros(len(years) - 1)

        for i in range(len(years)):
                if population[i] == population[-1]:
                        break
                growth_rate[i] = ((population[i + 1] - population[i]) / population[i]) * 100

        return growth_rate

# Start series of options for plotting data to model comaprisons
if do_plot_asfr:
        '''
        Plot age-specific fertility rate between model and data
        '''
        # Print ASFR form model in output
        for key in age_bin_map.keys():
            print(f'ASFR (annual) for age bin {key} in the last year of the sim: {res["asfr"][key][-1]}')

        x = [1, 2, 3, 4, 5, 6, 7, 8]

        # Load data
        year = data_asfr[data_asfr['year'] == pars['end_year']]
        asfr_data = year.drop(['year', '50-54'], axis=1).values.tolist()[0]

        x_labels = []
        asfr_model = []

        # Extract from model
        for key in age_bin_map.keys():
                x_labels.append(key)
                asfr_model.append(res['asfr'][key][-1])

        # Plot
        fig, ax = pl.subplots()
        kw = dict(lw=3, alpha=0.7, markersize=10)
        ax.plot(x, asfr_data, marker='^', color='black', label="UN data", **kw)
        ax.plot(x, asfr_model, marker='*', color='cornflowerblue', label="FPsim", **kw)
        pl.xticks(x, x_labels)
        pl.ylim(bottom=-10)
        ax.set_title('Age specific fertility rate per 1000 woman years')
        ax.set_xlabel('Age')
        ax.set_ylabel('ASFR in 2019')
        ax.legend(frameon=False)
        sc.boxoff()

        if do_save:
                pl.savefig('figs/asfr.png')

        pl.show()

if do_plot_methods:
        '''
        Plots both dichotomous method use and non-use and contraceptive mix
        '''

        # Pull method definitions from parameters file
        # Method map; this remains constant across locations. True indicates modern method,
        # and False indicates traditional method
        methods_map_model = {  # Index, modern, efficacy
        'None': [0, False],
        'Withdrawal': [1, False],
        'Other traditional': [2, False],
        # 1/2 periodic abstinence, 1/2 other traditional approx.  Using rate from periodic abstinence
        'Condoms': [3, True],
        'Pill': [4, True],
        'Injectables': [5, True],
        'Implants': [6, True],
        'IUDs': [7, True],
        'BTL': [8, True],
        'Other modern': [9, True],
        }

        # Setup
        model_labels_all = list(methods_map_model.keys())
        model_labels_methods = sc.dcp(model_labels_all)
        model_labels_methods = model_labels_methods[1:]

        model_method_counts = sc.odict().make(keys=model_labels_all, vals=0.0)

        # Extract from model
        for i in range(len(ppl)):
                if ppl.alive[i] and not ppl.sex[i] and ppl.age[i] >= min_age and ppl.age[i] < max_age:
                        model_method_counts[ppl.method[i]] += 1

        model_method_counts[:] /= model_method_counts[:].sum()


        # Method mix from data - country PMA data (mix_{country}.csv)
        data_methods_mix = {
                'Withdrawal': data_methods.loc[data_methods['method'] == 'withdrawal', 'perc'].iloc[0],
                'Other traditional': data_methods.loc[data_methods['method'] == 'other traditional', 'perc'].iloc[0],
                'Condoms': data_methods.loc[data_methods['method'] == 'condoms', 'perc'].iloc[0],
                'Pill': data_methods.loc[data_methods['method'] == 'pill', 'perc'].iloc[0],
                'Injectables': data_methods.loc[data_methods['method'] == 'injectables', 'perc'].iloc[0],
                'Implants': data_methods.loc[data_methods['method'] == 'implant', 'perc'].iloc[0],
                'IUDs': data_methods.loc[data_methods['method'] == 'IUD', 'perc'].iloc[0],
                'BTL': data_methods.loc[data_methods['method'] == 'BTL/vasectomy', 'perc'].iloc[0],
                'Other modern': data_methods.loc[data_methods['method'] == 'other modern', 'perc'].iloc[0]
        }

        # Method use from data - country PMA data (use_{country}.csv)
        no_use = use.loc[0, 'perc']
        any_method = use.loc[1, 'perc']
        data_methods_use = {
                'No use': no_use,
                'Any method': any_method
        }

        # Plot bar charts of method mix and use among users

        # Calculate users vs non-users in model
        model_methods_mix = sc.dcp(model_method_counts)
        model_use = [model_methods_mix['None'], model_methods_mix[1:].sum()]
        model_use_percent = [i * 100 for i in model_use]

        # Calculate mix within users in model
        model_methods_mix['None'] = 0.0
        model_users_sum = model_methods_mix[:].sum()
        model_methods_mix[:] /= model_users_sum
        mix_model = model_methods_mix.values()[1:]
        mix_percent_model = [i * 100 for i in mix_model]

        # Set method use and mix from data
        mix_percent_data = list(data_methods_mix.values())
        data_use_percent = list(data_methods_use.values())

        # Set up plotting
        use_labels = list(data_methods_use.keys())
        df_mix = pd.DataFrame({'PMA': mix_percent_data, 'FPsim': mix_percent_model}, index=model_labels_methods)
        df_use = pd.DataFrame({'PMA': data_use_percent, 'FPsim': model_use_percent}, index=use_labels)

        # Plot mix
        ax = df_mix.plot.barh(color={'PMA':'black', 'FPsim':'cornflowerblue'})
        ax.set_xlabel('Percent users')
        ax.set_title('Contraceptive method mix model vs data')
        if do_save:
                pl.savefig("figs/method_mix.png", bbox_inches='tight', dpi=100)

        # Plot use
        ax = df_use.plot.barh(color={'PMA':'black', 'FPsim':'cornflowerblue'})
        ax.set_xlabel('Percent')
        ax.set_title('Contraceptive method use model vs data')
        if do_save:
                pl.savefig("figs/method_use.png", bbox_inches='tight', dpi=100)


if do_plot_skyscrapers:
        '''
        Plot an age-parity distribution for model vs data
        '''

        dataset = 'PMA 2022'  # Data to compare to for skyscrapers, can also use DHS 2014

        # Set up
        age_keys = list(age_bin_map.keys())[1:]
        age_bins = pl.arange(min_age, max_age, bin_size)
        parity_bins = pl.arange(0, 7) # Plot up to parity 6
        n_age = len(age_bins)
        n_parity = len(parity_bins)
        x_age = pl.arange(n_age)
        x_parity = pl.arange(n_parity)  # Should be the same

        # Load data
        data_parity_bins = pl.arange(0,7)
        sky_raw_data = skyscrapers
        sky_raw_data = sky_raw_data[sky_raw_data['dataset'] == dataset]

        sky_parity = sky_raw_data['parity'].to_numpy()
        sky_props = sky_raw_data['percentage'].to_numpy()


        sky_arr = sc.odict()

        sky_arr['Data'] = pl.zeros((len(age_keys), len(parity_bins)))

        proportion = 0
        age_name = ''
        for age, row in sky_raw_data.iterrows():
                if row.age in age_keys:
                        age_ind = age_keys.index(row.age)
                        sky_arr['Data'][age_ind, row.parity] = row.percentage


        # Extract from model
        sky_arr['Model'] = pl.zeros((len(age_bins), len(parity_bins)))
        for i in range(len(ppl)):
                if ppl.alive[i] and not ppl.sex[i] and ppl.age[i] >= min_age and ppl.age[i] < max_age:
                        age_bin = sc.findinds(age_bins <= ppl.age[i])[-1]
                        parity_bin = sc.findinds(parity_bins <= ppl.parity[i])[-1]
                        sky_arr['Model'][age_bin, parity_bin] += 1


        # Normalize
        for key in ['Data', 'Model']:
                sky_arr[key] /= sky_arr[key].sum() / 100

        # Find diff to help visualize in plotting
        sky_arr['Diff: data - model'] = sky_arr['Data']-sky_arr['Model']

        # Plot skyscrapers
        for key in ['Data', 'Model', 'Diff: data - model']:
                fig = pl.figure(figsize=(20, 14))

                sc.bar3d(fig=fig, data=sky_arr[key], cmap='jet')
                pl.xlabel('Age', fontweight='bold')
                pl.ylabel('Parity', fontweight='bold')
                pl.title(f'Age-parity plot for the {key.lower()}\n\n', fontweight='bold')
                pl.gca().set_xticks(pl.arange(n_age))
                pl.gca().set_yticks(pl.arange(n_parity))
                pl.gca().set_xticklabels(age_bins)
                pl.gca().set_yticklabels(parity_bins)
                pl.gca().view_init(30, 45)
                pl.draw()


                if do_save:
                        pl.savefig('figs/skyscrapers_' + str(key.lower()) + '.png')

                pl.show()


if do_plot_cpr:

        '''
        Plot contraceptive prevalence rate for model vs data
        '''
        # Import data
        data_cpr = data_cpr[data_cpr['year'] <= pars['end_year']] # Restrict years to plot

        # Plot
        pl.plot(data_cpr['year'], data_cpr['cpr'], label='UN Data Portal', color='black')
        pl.plot(res['t'], res['cpr']*100, label='FPsim', color='cornflowerblue')
        pl.xlabel('Year')
        pl.ylabel('Percent')
        pl.title(f'Contraceptive Prevalence Rate in Data vs Model - {country}')
        pl.legend()

        if do_save:
                pl.savefig('figs/cpr_over_sim.png')

        pl.show()


if do_plot_tfr:
        '''
        Plot total fertility rate for model vs data
        '''

        # Import data
        #data_tfr = pd.read_csv(f'{country}_tfr.csv')

        # Plot
        pl.plot(data_tfr['year'], data_tfr['tfr'], label='World Bank', color='black')
        pl.plot(res['tfr_years'], res['tfr_rates'], label='FPsim', color='cornflowerblue')
        pl.xlabel('Year')
        pl.ylabel('Rate')
        pl.title(f'Total Fertility Rate in Data vs Model - {country}')
        pl.legend()

        if do_save:
                pl.savefig('figs/tfr_over_sim.png')

        pl.show()

if do_plot_pop_growth:
        '''
        Plot annual population growth rate for model vs data
        '''

        # Import data
        data_popsize = data_popsize[data_popsize['year'] <= pars['end_year']]  # Restrict years to plot

        data_pop_years = data_popsize['year'].to_numpy()
        data_population = data_popsize['population'].to_numpy()

        # Extract from model
        model_growth_rate = pop_growth_rate(res['tfr_years'], res['pop_size'])

        data_growth_rate = pop_growth_rate(data_pop_years, data_population)

        # Plot
        pl.plot(data_pop_years[1:], data_growth_rate, label='World Bank', color='black')
        pl.plot(res['tfr_years'][1:], model_growth_rate, label='FPsim', color='cornflowerblue')
        pl.xlabel('Year')
        pl.ylabel('Rate')
        pl.title(f'Population Growth Rate Data vs Model - {country}')
        pl.legend()

        if do_save:
                pl.savefig('figs/popgrowth_over_sim.png')

        pl.show()


if do_plot_birth_space_afb:
        '''
        Plot birth space and age at first birth for model vs data
        '''

        # Set up
        spacing_bins = sc.odict({'0-12': 0, '12-24': 1, '24-48': 2, '>48': 4})  # Spacing bins in years
        model_age_first = []
        model_spacing = []
        model_spacing_counts = sc.odict().make(keys=spacing_bins.keys(), vals=0.0)
        data_spacing_counts = sc.odict().make(keys=spacing_bins.keys(), vals=0.0)


        # Extract age at first birth and birth spaces from model
        for i in range(len(ppl)):
                if ppl.alive[i] and not ppl.sex[i] and ppl.age[i] >= min_age and ppl.age[i] < max_age:
                        if len(ppl.dobs[i]) == 0:
                                model_age_first.append(float('inf'))
                        if len(ppl.dobs[i]) and ppl.age[i] >= first_birth_age:
                                model_age_first.append(ppl.dobs[i][0])
                        if len(ppl.dobs[i]) > 1:
                                for d in range(len(ppl.dobs[i]) - 1):
                                        space = ppl.dobs[i][d + 1] - ppl.dobs[i][d]
                                        ind = sc.findinds(space > spacing_bins[:])[-1]
                                        model_spacing_counts[ind] += 1
                                        model_spacing.append(space)

        # Normalize model birth space bin counts to percentages
        model_spacing_counts[:] /= model_spacing_counts[:].sum()
        model_spacing_counts[:] *= 100

        age_first_birth_model = pd.DataFrame(data=model_age_first)

        # Extract birth spaces and age at first birth from data
        for i, j in data_spaces.iterrows():
                space = j['space_mo'] / mpy
                ind = sc.findinds(space > spacing_bins[:])[-1]
                data_spacing_counts[ind] += j['Freq']

        age_first_birth_data = pd.DataFrame(data=data_afb)

        # Normalize dat birth space bin counts to percentages
        data_spacing_counts[:] /= data_spacing_counts[:].sum()
        data_spacing_counts[:] *= 100

        # Plot age at first birth (histogram with KDE)
        sns.histplot(data=age_first_birth_model, stat='proportion', kde=True, binwidth=1, color='cornflowerblue', label='FPsim')
        sns.histplot(x=age_first_birth_data['afb'], stat='proportion', kde=True, weights=age_first_birth_data['wt'], binwidth=1, color='dimgrey', label='DHS data')
        pl.xlabel('Age at first birth')
        pl.legend()

        if do_save:
                pl.savefig('figs/age_first_birth.png', bbox_inches='tight', dpi=100)

        pl.show()


        # Plot birth space bins with diff
        data_dict['spacing_bins'] = np.array(data_spacing_counts.values())
        model_dict['spacing_bins'] = np.array(model_spacing_counts.values())

        diff = model_dict['spacing_bins'] - data_dict['spacing_bins']

        res_bins = np.array([[model_dict['spacing_bins']], [data_dict['spacing_bins']], [diff]])

        bins_frame = pd.DataFrame(
                {'Model': model_dict['spacing_bins'], 'Data': data_dict['spacing_bins'], 'Diff': diff},
                index=spacing_bins.keys())

        print(bins_frame) # Print in output, remove if not needed

        ax = bins_frame.plot.barh(color={'Data': 'black', 'Model': 'cornflowerblue', 'Diff': 'red'})
        ax.set_xlabel('Percent of live birth spaces')
        ax.set_ylabel('Birth space in months')
        ax.set_title(f'Birth space bins calibration - {country}')

        if do_save:
                pl.savefig(f'figs/birth_space_bins_{country}.png', bbox_inches='tight', dpi=100)

        pl.show()

sc.toc()
print('Done.')


'''
Leaving code here in case we want to plot age-parity distribution differently with colormesh


        fig, axs = pl.subplots(3)

        fig.suptitle('Age Parity Distribution')

        axs[0].pcolormesh(age_bins, parity_bins, sky_arr.Data.transpose(), shading='nearest', cmap='turbo')
        axs[0].set_aspect(1. / ax.get_data_ratio())  # Make square
        axs[0].set_title('Age-parity plot: Kenya PMA 2022')
        axs[0].set_xlabel('Age')
        ax[0].set_ylabel('Parity')

        axs[1].pcolormesh(age_bins, parity_bins, sky_arr.Model.transpose(), shading='nearest', cmap='turbo')
        axs[1].set_aspect(1. / ax.get_data_ratio())  # Make square
        axs[1].set_title('Age-parity plot: Kenya PMA 2022')
        axs[1].set_xlabel('Age')
        axs[1].set_ylabel('Parity')

        pl.show()

'''