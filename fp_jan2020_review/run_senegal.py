# Run all analyses for Senegal

import pylab as pl
import pandas as pd
import sciris as sc
import lemod_fp as lfp
import senegal_parameters as sp

# Set parameters
do_run              = 1
do_plot_popsize     = 1
do_plot_pyramids    = 1
do_plot_skyscrapers = 1
do_save             = 1

year_str = '2015'
pop_pyr_2015_fn = sp.abspath('dropbox/Population_Pyramid_-_All.csv')
skyscrapers_fn = sp.abspath('dropbox/Skyscrapers-All-DHS.csv')

if do_run:
    pars = sp.make_pars()
    sim = lfp.Sim(pars=pars)
    
    def add_long_acting(sim):
        print('Added long-acting intervention')
        for person in sim.people.values():
            person.method = 'implant'
    
    def urhi(sim):
        print('Added URHI')
        switching = sim.pars['switching']
        print(switching)
        for i,method1 in enumerate(switching.keys()):
            switching[method1][0] *= 0.0
            switching[method1][:] = switching[method1][:]/switching[method1][:].sum()
        sim.pars['switching'] = switching
        print(switching)
        for person in sim.people.values():
            person.pars = sim.pars

    def serialize(sim):
        sc.saveobj(sp.abspath('serialized_pop.obj'), sim.people)

    def deserialize(sim):
        sim.people = sc.loadobj(sp.abspath('serialized_pop.obj'))

    
    # sim.add_intervention(intervention=add_long_acting, year=2000)
    # sim.add_intervention(intervention=urhi, year=2000)
    # sim.add_intervention(intervention=serialize, year=2000)
    # sim.add_intervention(intervention=deserialize, year=2010)
    sim.run()
    people = list(sim.people.values()) # Pull out people
    
    if do_plot_popsize:
        
        # Default plots
        fig = sim.plot()
        
        # Population size plot
        ax = fig.axes[-1] 
        ax.scatter(sp.years, sp.popsize, c='k', label='Data', zorder=1000)
        pl.legend()
        if do_save:
            pl.savefig(sp.abspath('figs/senegal_popsize.png'))
    
    if do_plot_pyramids:
        fig2 = pl.figure(figsize=(16,16))
        
        # Load 2015 population pyramid from DHS
        min_age = 15
        max_age = 50
        bin_size = 5
        pop_pyr_2015  = pd.read_csv(pop_pyr_2015_fn, header=None)
        pop_pyr_2015 = pop_pyr_2015[pop_pyr_2015[0]==year_str]
        bins = pl.arange(min_age, max_age, bin_size)
        pop_props_2015 = pop_pyr_2015[2].to_numpy()
        
        plotstyle = {'marker':'o', 'lw':3}
        
        counts = pl.zeros(len(bins))
        for person in people:
            if person.alive:
                bininds = sc.findinds(bins<=person.age) # Could be refactored
                if len(bininds) and person.age < max_age:
                    counts[bininds[-1]] += 1
        counts = counts/counts.sum()
        
        x = pl.hstack([bins, bins[::-1]])
        PP = pl.hstack([pop_props_2015,-pop_props_2015[::-1]])
        CC = pl.hstack([counts,-counts[::-1]])
        
        pl.plot(PP, x, c='b', label='2015 data', **plotstyle)
        pl.plot(CC, x, c='g', label='Model', **plotstyle)
        
        pl.legend()
        pl.xlabel('Proportion')
        pl.ylabel('Age')
        pl.title('Age pyramid')
        sc.setylim()
        
        if do_save:
            pl.savefig(sp.abspath('figs/senegal_pyramids.png'))
            
       

    if do_plot_skyscrapers:
        
        # Set up
        min_age = 15
        max_age = 50
        bin_size = 5
        age_bins = pl.arange(min_age, max_age, bin_size)
        parity_bins = pl.arange(0,7)
        n_age = len(age_bins)
        n_parity = len(parity_bins)
        x_age = pl.arange(n_age)
        x_parity = pl.arange(n_parity) # Should be the same
        
        # Load data
        data_parity_bins = pl.arange(0,18)
        sky_raw_data  = pd.read_csv(skyscrapers_fn, header=None)
        sky_raw_data = sky_raw_data[sky_raw_data[0]==year_str]
        sky_parity = sky_raw_data[2].to_numpy()
        sky_props = sky_raw_data[3].to_numpy()
        sky_arr = sc.odict()
        
        sky_arr['Data'] = pl.zeros((len(age_bins), len(parity_bins)))
        count = -1
        for age_bin in x_age:
            for dpb in data_parity_bins:
                count += 1
                parity_bin = min(n_parity-1, dpb)
                sky_arr['Data'][age_bin, parity_bin] += sky_props[count]
        assert count == len(sky_props)-1 # Ensure they're the right length
                
        
        # Extract from model
        sky_arr['Model'] = pl.zeros((len(age_bins), len(parity_bins)))
        for person in people:
            if not person.sex and person.age>=min_age and person.age<max_age:
                age_bin = sc.findinds(age_bins<=person.age)[-1]
                parity_bin = sc.findinds(parity_bins<=person.parity)[-1]
                sky_arr['Model'][age_bin, parity_bin] += 1
        
        # Normalize
        for key in ['Data', 'Model']:
            sky_arr[key] /= sky_arr[key].sum() / 100
        
        # Plot skyscrapers
        for key in ['Data', 'Model']:
            fig = pl.figure(figsize=(20,14))
            
            sc.bar3d(fig=fig, data=sky_arr[key], cmap='jet')
            pl.xlabel('Age')
            pl.ylabel('Parity')
            pl.title(f'Age-parity plot for {key}')
            pl.gca().set_xticks(pl.arange(n_age))
            pl.gca().set_yticks(pl.arange(n_parity))
            pl.gca().set_xticklabels(age_bins)
            pl.gca().set_yticklabels(parity_bins)
            pl.gca().view_init(30,45)
            pl.draw()
            if do_save:
                pl.savefig(sp.abspath(f'figs/senegal_skyscrapers_{key}.png'))
                
        
        # Plot sums
        fig = pl.figure(figsize=(20,14))
        labels = ['Parity', 'Age']
        x_axes = [x_parity, x_age]
        offsets = [0, 0.4]
        for i in range(2):
            pl.subplot(2,1,i+1)
            for k,key in enumerate(['Data', 'Model']):
                y_data = sky_arr[key].sum(axis=i)
                # y_data = y_data/y_data.sum()
                pl.bar(x_axes[i]+offsets[k], y_data, width=0.4, label=key)
                pl.xlabel(labels[i])
                pl.ylabel('Percentage of population')
                pl.title(f'Population by: {labels[i]}')
                pl.legend()
                if do_save:
                    pl.savefig(sp.abspath(f'figs/senegal_age_parity_sums.png'))
    
    
            
    
print('Done.')
