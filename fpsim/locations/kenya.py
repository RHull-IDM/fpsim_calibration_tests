'''
Set the parameters for FPsim, specifically for Kenya.
'''

import numpy as np
import pandas as pd
import sciris as sc
from scipy import interpolate as si
from .. import defaults as fpd

# %% Housekeeping

thisdir = sc.path(sc.thisdir())  # For loading CSV files


def scalar_pars():
    scalar_pars = {
        # Basic parameters
        'location': 'kenya',
        'n_agents': 1_000,  # Number of agents
        'scaled_pop': None,  # Scaled population / total population size
        'start_year': 1960,  # Start year of simulation
        'end_year': 2020,  # End year of simulation
        'timestep': 1,  # The simulation timestep in months
        'method_timestep': 1,  # How many simulation timesteps to go for every method update step
        'seed': 1,  # Random seed
        'verbose': 1,  # How much detail to print during the simulation
        'track_switching': 0,  # Whether to track method switching
        'track_as': 0,  # Whether to track age-specific channels
        'short_int': 24,  # Duration of a short birth interval between live births in months
        'low_age_short_int': 0,  # age limit for tracking the age-specific short birth interval
        'high_age_short_int': 20,  # age limit for tracking the age-specific short birth interval

        # Age limits (in years)
        'method_age': 15,
        'age_limit_fecundity': 50,
        'max_age': 99,

        # Durations (in months)
        'switch_frequency': 12,  # How frequently to check for changes to contraception
        'end_first_tri': 3,
        'preg_dur_low': 9,
        'preg_dur_high': 9,
        'postpartum_dur': 23,
        'breastfeeding_dur_mu': 11.4261936291137,  # Location parameter of gumbel distribution. Requires children's recode DHS file, see data_processing/breastfeedin_stats.R
        'breastfeeding_dur_beta': 7.5435309020483, # Location parameter of gumbel distribution. Requires children's recode DHS file, see data_processing/breastfeedin_stats.R 
        'max_lam_dur': 5,  # Duration of lactational amenorrhea
        'short_int': 24,  # Duration of a short birth interval between live births in months
        'low_age_short_int': 0,  # age limit for tracking the age-specific short birth interval
        'high_age_short_int': 20,  # age limit for tracking the age-specific short birth interval

        # Pregnancy outcomes
        'abortion_prob': 0.201,
        # From https://bmcpregnancychildbirth.biomedcentral.com/articles/10.1186/s12884-015-0621-1, % of all pregnancies calculated
        'twins_prob': 0.016,  # From https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0025239
        'LAM_efficacy': 0.98,  # From Cochrane review: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC6823189/
        'maternal_mortality_factor': 1,

        # Fecundity and exposure
        'fecundity_var_low': 0.7,
        'fecundity_var_high': 1.1,
        'high_parity': 1,
        'high_parity_nonuse': 1,
        'primary_infertility': 0.05,
        'exposure_factor': 1.0,  # Overall exposure correction factor
        'restrict_method_use': 0, # If 1, only allows agents to select methods when sexually active within 12 months
                                   # and at fated debut age.  Contraceptive matrix probs must be changed to turn on

        # MCPR
        'mcpr_growth_rate': 0.02,  # The year-on-year change in MCPR after the end of the data
        'mcpr_max': 0.90,  # Do not allow MCPR to increase beyond this
        'mcpr_norm_year': 2020,  # Year to normalize MCPR trend to 1
    }
    return scalar_pars


def data2interp(data, ages, normalize=False):
    ''' Convert unevenly spaced data into an even spline interpolation '''
    model = si.interp1d(data[0], data[1])
    interp = model(ages)
    if normalize:
        interp = np.minimum(1, np.maximum(0, interp))
    return interp


# TODO- these need to be changed for Kenya calibration and commented with their data source
def filenames():
    ''' Data files for use with calibration, etc -- not needed for running a sim '''
    files = {}
    files['base'] = sc.thisdir(aspath=True) / 'kenya'
    files['basic_dhs'] = 'kenya_basic_dhs.yaml' # From World Bank https://data.worldbank.org/indicator/SH.STA.MMRT?locations=KE
    files['popsize'] = 'kenya_popsize.csv' # Downloaded from World Bank: https://data.worldbank.org/indicator/SP.POP.TOTL?locations=KE
    files['mcpr'] = 'kenya_cpr.csv'  # From UN Population Division Data Portal, married women 1970-1986, all women 1990-2030
    files['tfr'] = 'kenya_tfr.csv'   # From World Bank https://data.worldbank.org/indicator/SP.DYN.TFRT.IN?locations=KE
    files['asfr'] = 'kenya_asfr.csv' # From UN World Population Prospects 2022: https://population.un.org/wpp/Download/Standard/Fertility/
    files['skyscrapers'] = 'kenya_skyscrapers.csv' # Choose from either DHS 2014 or PMA 2022
    #files['spacing'] = 'BirthSpacing.obj'
    #files['methods'] = 'Method_v312.csv'
    return files


# %% Demographics and pregnancy outcome

def age_pyramid():
    '''
    Starting age bin, male population, female population
    Data are from World Population Prospects
    https://population.un.org/wpp/Download/Standard/Population/
     '''
    pyramid = np.array([[0, 801895, 800503],  # Kenya 1960
                        [5, 620524, 625424],
                        [10, 463547, 464020],
                        [15, 333241, 331921],
                        [20, 307544, 309057],
                        [25, 292141, 287621],
                        [30, 247826, 236200],
                        [35, 208416, 190234],
                        [40, 177914, 162057],
                        [45, 156771, 138943],
                        [50, 135912, 123979],
                        [55, 108653, 111939],
                        [60, 85407, 94582],
                        [65, 61664, 71912],
                        [70, 40797, 49512],
                        [75, 22023, 29298],
                        [80, 11025, 17580],
                        ], dtype=float)

    return pyramid


def age_mortality():
    '''
    Age-dependent mortality rates taken from UN World Population Prospects 2022.  From probability of dying each year.
    https://population.un.org/wpp/
    Used CSV WPP2022_Life_Table_Complete_Medium_Female_1950-2021, Kenya, 2010
    Used CSV WPP2022_Life_Table_Complete_Medium_Male_1950-2021, Kenya, 2010
    Mortality rate trend from crude death rate per 1000 people, also from UN Data Portal, 1950-2030:
    https://population.un.org/dataportal/data/indicators/59/locations/404/start/1950/end/2030/table/pivotbylocation
    Projections go out until 2030, but the csv file can be manually adjusted to remove any projections and stop at your desired year
    '''
    data_year = 2010
    mortality_data = pd.read_csv(thisdir / 'kenya' / 'mortality_prob_kenya.csv')
    mortality_trend = pd.read_csv(thisdir / 'kenya' / 'mortality_trend_kenya.csv')

    mortality = {
        'ages': mortality_data['age'].to_numpy(),
        'm': mortality_data['male'].to_numpy(),
        'f': mortality_data['female'].to_numpy()
    }

    mortality['year'] = mortality_trend['year'].to_numpy()
    mortality['probs'] = mortality_trend['crude_death_rate'].to_numpy()
    trend_ind = np.where(mortality['year'] == data_year)
    trend_val = mortality['probs'][trend_ind]

    mortality['probs'] /= trend_val  # Normalize around data year for trending
    m_mortality_spline_model = si.splrep(x=mortality['ages'],
                                         y=mortality['m'])  # Create a spline of mortality along known age bins
    f_mortality_spline_model = si.splrep(x=mortality['ages'], y=mortality['f'])
    m_mortality_spline = si.splev(fpd.spline_ages,
                                  m_mortality_spline_model)  # Evaluate the spline along the range of ages in the model with resolution
    f_mortality_spline = si.splev(fpd.spline_ages, f_mortality_spline_model)
    m_mortality_spline = np.minimum(1, np.maximum(0, m_mortality_spline))  # Normalize
    f_mortality_spline = np.minimum(1, np.maximum(0, f_mortality_spline))

    mortality['m_spline'] = m_mortality_spline
    mortality['f_spline'] = f_mortality_spline

    return mortality


def maternal_mortality():
    '''
    From World Bank indicators for maternal mortality ratio (modeled estimate) per 100,000 live births:
    https://data.worldbank.org/indicator/SH.STA.MMRT?locations=KE
    '''

    data = np.array([
        [2000, 708],
        [2001, 702],
        [2002, 692],
        [2003, 678],
        [2004, 653],
        [2005, 618],
        [2006, 583],
        [2007, 545],
        [2008, 513],
        [2009, 472],
        [2010, 432],
        [2011, 398],
        [2012, 373],
        [2013, 364],
        [2014, 358],
        [2015, 353],
        [2016, 346],
        [2017, 342],

    ])

    maternal_mortality = {}
    maternal_mortality['year'] = data[:, 0]
    maternal_mortality['probs'] = data[:, 1] / 100000  # ratio per 100,000 live births
    # maternal_mortality['ages'] = np.array([16, 17,   19, 22,   25, 50])
    # maternal_mortality['age_probs'] = np.array([2.28, 1.63, 1.3, 1.12, 1.0, 1.0]) #need to be added

    return maternal_mortality


def infant_mortality():
    '''
    From World Bank indicators for infant mortality (< 1 year) for Kenya, per 1000 live births
    From API_SP.DYN.IMRT.IN_DS2_en_excel_v2_1495452.numbers
    Adolescent increased risk of infant mortality gradient taken
    from Noori et al for Sub-Saharan African from 2014-2018.  Odds ratios with age 23-25 as reference group:
    https://www.medrxiv.org/content/10.1101/2021.06.10.21258227v1
    '''

    data = np.array([
        [1960, 118.1],
        [1961, 113.7],
        [1962, 109.8],
        [1963, 106.5],
        [1964, 103.8],
        [1965, 101.6],
        [1966, 99.8],
        [1967, 98.0],
        [1968, 96.3],
        [1969, 94.5],
        [1970, 92.6],
        [1971, 90.8],
        [1972, 88.8],
        [1973, 86.7],
        [1974, 84.5],
        [1975, 82.2],
        [1976, 79.8],
        [1977, 77.4],
        [1978, 75.0],
        [1979, 72.7],
        [1980, 70.5],
        [1981, 68.5],
        [1982, 66.7],
        [1983, 65.1],
        [1984, 63.8],
        [1985, 62.9],
        [1986, 62.4],
        [1987, 62.4],
        [1988, 62.8],
        [1989, 63.7],
        [1990, 64.8],
        [1991, 66.1],
        [1992, 67.2],
        [1993, 67.9],
        [1994, 68.0],
        [1995, 67.6],
        [1996, 66.5],
        [1997, 65.1],
        [1998, 63.5],
        [1999, 61.7],
        [2000, 59.7],
        [2001, 57.6],
        [2002, 55.4],
        [2003, 53.1],
        [2004, 50.7],
        [2005, 48.1],
        [2006, 45.8],
        [2007, 43.8],
        [2008, 41.4],
        [2009, 40.3],
        [2010, 39.4],
        [2011, 38.6],
        [2012, 38.2],
        [2013, 37.5],
        [2014, 36.5],
        [2015, 35.3],
        [2016, 34.5],
        [2017, 33.9],
        [2018, 32.8],
        [2019, 31.9]
    ])

    infant_mortality = {}
    infant_mortality['year'] = data[:, 0]
    infant_mortality['probs'] = data[:, 1] / 1000  # Rate per 1000 live births, used after stillbirth is filtered out
    infant_mortality['ages'] = np.array([16, 17, 19, 22, 25, 50])
    infant_mortality['age_probs'] = np.array([2.28, 1.63, 1.3, 1.12, 1.0, 1.0])

    return infant_mortality


def miscarriage():
    '''
    Returns a linear interpolation of the likelihood of a miscarriage
    by age, taken from data from Magnus et al BMJ 2019: https://pubmed.ncbi.nlm.nih.gov/30894356/
    Data to be fed into likelihood of continuing a pregnancy once initialized in model
    Age 0 and 5 set at 100% likelihood.  Age 10 imputed to be symmetrical with probability at age 45 for a parabolic curve
    '''
    miscarriage_rates = np.array([[0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50],
                                  [1, 1, 0.569, 0.167, 0.112, 0.097, 0.108, 0.167, 0.332, 0.569, 0.569]])
    miscarriage_interp = data2interp(miscarriage_rates, fpd.spline_preg_ages)
    return miscarriage_interp


def stillbirth():
    '''
    From Report of the UN Inter-agency Group for Child Mortality Estimation, 2020
    https://childmortality.org/wp-content/uploads/2020/10/UN-IGME-2020-Stillbirth-Report.pdf

    Age adjustments come from an extension of Noori et al., which were conducted June 2022.
    '''

    data = np.array([
        [2000, 22.5],
        [2010, 20.6],
        [2019, 19.7],
    ])

    stillbirth_rate = {}
    stillbirth_rate['year'] = data[:, 0]
    stillbirth_rate['probs'] = data[:, 1] / 1000  # Rate per 1000 total births
    stillbirth_rate['ages'] = np.array([15, 16, 17, 19, 20, 28, 31, 36, 50])
    stillbirth_rate['age_probs'] = np.array([3.27, 1.64, 1.85, 1.39, 0.89, 1.0, 1.5, 1.55, 1.78])  # odds ratios

    return stillbirth_rate


# %% Fecundity

def female_age_fecundity():
    '''
    Use fecundity rates from PRESTO study: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5712257/
    Fecundity rate assumed to be approximately linear from onset of fecundity around age 10 (average age of menses 12.5) to first data point at age 20
    45-50 age bin estimated at 0.10 of fecundity of 25-27 yr olds
    '''
    fecundity = {
        'bins': np.array([0., 5, 10, 15, 20, 25, 28, 31, 34, 37, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 99]),
        'f': np.array([0., 0, 0, 65, 70.8, 79.3, 77.9, 76.6, 74.8, 67.4, 55.5, 7.9, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])}
    fecundity[
        'f'] /= 100  # Conceptions per hundred to conceptions per woman over 12 menstrual cycles of trying to conceive

    fecundity_interp_model = si.interp1d(x=fecundity['bins'], y=fecundity['f'])
    fecundity_interp = fecundity_interp_model(fpd.spline_preg_ages)
    fecundity_interp = np.minimum(1, np.maximum(0, fecundity_interp))  # Normalize to avoid negative or >1 values

    return fecundity_interp


def fecundity_ratio_nullip():
    '''
    Returns an array of fecundity ratios for a nulliparous woman vs a gravid woman
    from PRESTO study: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5712257/
    Approximates primary infertility and its increasing likelihood if a woman has never conceived by age
    '''
    fecundity_ratio_nullip = np.array([[0, 5, 10, 12.5, 15, 18, 20, 25, 30, 34, 37, 40, 45, 50],
                                       [1, 1, 1, 1, 1, 1, 1, 0.96, 0.95, 0.71, 0.73, 0.42, 0.42, 0.42]])
    fecundity_nullip_interp = data2interp(fecundity_ratio_nullip, fpd.spline_preg_ages)

    return fecundity_nullip_interp


def lactational_amenorrhea():
    '''
    Returns an array of the percent of breastfeeding women by month postpartum 0-11 months who meet criteria for LAM:
    Exclusively breastfeeding (bf + water alone), menses have not returned.  Extended out 5-11 months to better match data
    as those women continue to be postpartum insusceptible.
    From DHS Kenya 2014 calendar data
    '''
    data = np.array([
        [0, 0.9557236],
        [1, 0.8889493],
        [2, 0.7040052],
        [3, 0.5332317],
        [4, 0.4115276],
        [5, 0.2668908],
        [6, 0.1364079],
        [7, 0.0571638],
        [8, 0.0025502],
        [9, 0.0259570],
        [10, 0.0072750],
        [11, 0.0046938],
    ])

    lactational_amenorrhea = {}
    lactational_amenorrhea['month'] = data[:, 0]
    lactational_amenorrhea['rate'] = data[:, 1]

    return lactational_amenorrhea


# %% Pregnancy exposure

def sexual_activity():
    '''
    Returns a linear interpolation of rates of female sexual activity, defined as
    percentage women who have had sex within the last four weeks.
    From STAT Compiler DHS https://www.statcompiler.com/en/
    Using indicator "Timing of sexual intercourse"
    Includes women who have had sex "within the last four weeks"
    Excludes women who answer "never had sex", probabilities are only applied to agents who have sexually debuted
    Data taken from 2018 DHS, no trend over years for now
    Onset of sexual activity probabilities assumed to be linear from age 10 to first data point at age 15
    '''

    sexually_active = np.array([[0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50],
                                [0, 0, 0, 31.4, 55.0, 64.4, 69.6, 65.3, 60.7, 57.4, 57.4]])

    sexually_active[1] /= 100  # Convert from percent to rate per woman
    activity_ages = sexually_active[0]
    activity_interp_model = si.interp1d(x=activity_ages, y=sexually_active[1])
    activity_interp = activity_interp_model(fpd.spline_preg_ages)  # Evaluate interpolation along resolution of ages

    return activity_interp


def sexual_activity_pp():
    '''
    Returns an array of monthly likelihood of having resumed sexual activity within 0-35 months postpartum
    Uses 2014 Kenya DHS individual recode (postpartum (v222), months since last birth, and sexual activity within 30 days.
    Data is weighted.
    Limited to 23 months postpartum (can use any limit you want 0-23 max)
    Postpartum month 0 refers to the first month after delivery
    TODO-- Add code for processing this for other countries to data_processing
    '''

    postpartum_sex = np.array([
        [0, 0.08453],
        [1, 0.08870],
        [2, 0.40634],
        [3, 0.58030],
        [4, 0.52688],
        [5, 0.60641],
        [6, 0.58103],
        [7, 0.72973],
        [8, 0.62647],
        [9, 0.73497],
        [10, 0.60254],
        [11, 0.75723],
        [12, 0.73159],
        [13, 0.68409],
        [14, 0.74925],
        [15, 0.74059],
        [16, 0.70051],
        [17, 0.78479],
        [18, 0.74965],
        [19, 0.79351],
        [20, 0.77338],
        [21, 0.70340],
        [22, 0.72395],
        [23, 0.72202]
    ])



    postpartum_activity = {}
    postpartum_activity['month'] = postpartum_sex[:, 0]
    postpartum_activity['percent_active'] = postpartum_sex[:, 1]

    return postpartum_activity


def debut_age():
    '''
    Returns an array of weighted probabilities of sexual debut by a certain age 10-45.
    Data taken from DHS variable v531 (imputed age of sexual debut, imputed with data from age at first union)
    Use sexual_debut_age_probs.py under locations/data_processing to output for other DHS countries
    '''

    sexual_debut = np.array([
        [10.0, 0.008404629256166524],
        [11.0, 0.006795048697926663],
        [12.0, 0.026330525753311643],
        [13.0, 0.04440278185223372],
        [14.0, 0.08283157906888061],
        [15.0, 0.14377365580688461],
        [16.0, 0.13271744734209995],
        [17.0, 0.11915611658325072],
        [18.0, 0.13735481818469894],
        [19.0, 0.0841039265081519],
        [20.0, 0.07725867074164659],
        [21.0, 0.03982337306065369],
        [22.0, 0.031195559243867545],
        [23.0, 0.020750304422300126],
        [24.0, 0.014468030815585422],
        [25.0, 0.010870195645684769],
        [26.0, 0.007574195696769944],
        [27.0, 0.0034378402773621282],
        [28.0, 0.0031344552061394622],
        [29.0, 0.0018168079578966389],
        [30.0, 0.001385356426809007],
        [31.0, 0.0004912818135032509],
        [32.0, 0.00045904179812542576],
        [33.0, 0.0005049625590548578],
        [34.0, 0.000165858204720886],
        [35.0, 0.00019259487032758347],
        [36.0, 0.0002126920535675137],
        [37.0, 8.84428869703282e-05],
        [38.0, 5.07209448615522e-05],
        [39.0, 6.555458199225806e-05],
        [41.0, 0.00013980442816424654],
        [44.0, 4.372731039149624e-05]])

    debut_age = {}
    debut_age['ages'] = sexual_debut[:, 0]
    debut_age['probs'] = sexual_debut[:, 1]

    return debut_age


def exposure_age():
    '''
    Returns an array of experimental factors to be applied to account for
    residual exposure to either pregnancy or live birth by age.  Exposure to pregnancy will
    increase factor number and residual likelihood of avoiding live birth (mostly abortion,
    also miscarriage), will decrease factor number
    '''
    exposure_correction_age = np.array([[0, 5, 10, 12.5, 15, 18, 20, 25, 30, 35, 40, 45, 50],
                                        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]])
    exposure_age_interp = data2interp(exposure_correction_age, fpd.spline_preg_ages)

    return exposure_age_interp


def exposure_parity():
    '''
    Returns an array of experimental factors to be applied to account for residual exposure to either pregnancy
    or live birth by parity.
    '''
    exposure_correction_parity = np.array([[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 20],
                                           [1, 1, 1, 1, 1, 1, 1, 0.8, 0.5, 0.3, 0.15, 0.10, 0.05, 0.01]])
    exposure_parity_interp = data2interp(exposure_correction_parity, fpd.spline_parities)

    return exposure_parity_interp


def birth_spacing_pref():
    '''
    Returns an array of birth spacing preferences by closest postpartum month.
    Applied to postpartum pregnancy likelihoods.

    NOTE: spacing bins must be uniform!
    '''
    postpartum_spacing = np.array([
        [0, 1],
        [3, 1],
        [6, 1],
        [9, 1],
        [12, 1],
        [15, 1],
        [18, 1],
        [21, 1],
        [24, 1],
        [27, 1],
        [30, 1],
        [33, 1],
        [36, 1],
    ])

    # Calculate the intervals and check they're all the same
    intervals = np.diff(postpartum_spacing[:, 0])
    interval = intervals[0]
    assert np.all(
        intervals == interval), f'In order to be computed in an array, birth spacing preference bins must be equal width, not {intervals}'
    pref_spacing = {}
    pref_spacing['interval'] = interval  # Store the interval (which we've just checked is always the same)
    pref_spacing['n_bins'] = len(intervals)  # Actually n_bins - 1, but we're counting 0 so it's OK
    pref_spacing['months'] = postpartum_spacing[:, 0]
    pref_spacing['preference'] = postpartum_spacing[:, 1]  # Store the actual birth spacing data

    return pref_spacing


# %% Contraceptive methods

def methods():
    '''
    Names, indices, modern/traditional flag, and efficacies of contraceptive methods -- see also parameters.py
    Efficacy from Guttmacher, fp_prerelease/docs/gates_review/contraceptive-failure-rates-in-developing-world_1.pdf
    BTL failure rate from general published data
    Pooled efficacy rates for all women in this study: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC4970461/
    '''

    # Define method data
    data = {  # Index, modern, efficacy
        'None': [0, False, 0.000],
        'Withdrawal': [1, False, 0.866],
        'Other traditional': [2, False, 0.861],
        # 1/2 periodic abstinence, 1/2 other traditional approx.  Using rate from periodic abstinence
        'Condoms': [3, True, 0.946],
        'Pill': [4, True, 0.945],
        'Injectables': [5, True, 0.983],
        'Implants': [6, True, 0.994],
        'IUDs': [7, True, 0.986],
        'BTL': [8, True, 0.995],
        'Other modern': [9, True, 0.880],
        # SDM makes up about 1/2 of this, perfect use is 95% and typical is 88%.  EC also included here, efficacy around 85% https : //www.aafp.org/afp/2004/0815/p707.html
    }

    keys = data.keys()
    methods = {}
    methods['map'] = {k: data[k][0] for k in keys}
    methods['modern'] = {k: data[k][1] for k in keys}
    methods['eff'] = {k: data[k][2] for k in keys}

    # Age bins for different method switching matrices -- duplicated in defaults.py
    methods['age_map'] = {
        '<18': [0, 18],
        '18-20': [18, 20],
        '21-25': [20, 25],
        '26-35': [25, 35],
        '>35': [35, fpd.max_age + 1],  # +1 since we're using < rather than <=
    }

    # Data on trend in CPR over time in from Kenya, in %.
    # Taken from UN Population Division Data Portal, married women 1970-1986, all women 1990-2030
    # https://population.un.org/dataportal/data/indicators/1/locations/404/start/1950/end/2040/table/pivotbylocation
    # Projections go out until 2030, but the csv file can be manually adjusted to remove any projections and stop at your desired year
    cpr_data = pd.read_csv(thisdir / 'kenya' / 'kenya_cpr.csv')
    methods['mcpr_years'] = cpr_data['year'].to_numpy()
    methods['mcpr_rates'] = cpr_data['cpr'].to_numpy() / 100  # convert from percent to rate

    return methods


'''
For reference
def method_probs_senegal():
    
    It does leave Senegal matrices in place in the Kenya file for now. 
    We may want to test with these as we work through scenarios and calibration. 
    
    Define "raw" (un-normalized, un-trended) matrices to give transitional probabilities
    from 2018 DHS Senegal contraceptive calendar data.

    Probabilities in this function are annual probabilities of initiating (top row), discontinuing (first column),
    continuing (diagonal), or switching methods (all other entries).

    Probabilities at postpartum month 1 are 1 month transitional probabilities
    for starting a method after delivery.

    Probabilities at postpartum month 6 are 5 month transitional probabilities
    for starting or changing methods over the first 6 months postpartum.

    Data from Senegal DHS contraceptive calendars, 2017 and 2018 combined
    

    raw = {

        # Main switching matrix: all non-postpartum women
        'annual': {
            '<18': np.array([
                [0.9953, 0., 0.0002, 0.0012, 0.0002, 0.0017, 0.0014, 0.0001, 0., 0.],
                [0., 1.0000, 0., 0., 0., 0., 0., 0., 0., 0.],
                [0.0525, 0., 0.9475, 0., 0., 0., 0., 0., 0., 0.],
                [0.307, 0., 0., 0.693, 0., 0., 0., 0., 0., 0.],
                [0.5358, 0., 0., 0., 0.3957, 0.0685, 0., 0., 0., 0.],
                [0.3779, 0., 0., 0., 0.0358, 0.5647, 0.0216, 0., 0., 0.],
                [0.2003, 0., 0., 0., 0., 0., 0.7997, 0., 0., 0.],
                [0., 0., 0., 0., 0., 0., 0., 1.0000, 0., 0.],
                [0., 0., 0., 0., 0., 0., 0., 0., 1.0000, 0.],
                [0., 0., 0., 0., 0., 0., 0., 0., 0., 1.0000]]),
            '18-20': np.array([
                [0.9774, 0., 0.0014, 0.0027, 0.0027, 0.0104, 0.0048, 0.0003, 0., 0.0003],
                [0., 1.0000, 0., 0., 0., 0., 0., 0., 0., 0.],
                [0.3216, 0., 0.6784, 0., 0., 0., 0., 0., 0., 0.],
                [0.182, 0., 0., 0.818, 0., 0., 0., 0., 0., 0.],
                [0.4549, 0., 0., 0., 0.4754, 0.0463, 0.0234, 0., 0., 0.],
                [0.4389, 0., 0.0049, 0.0099, 0.0196, 0.5218, 0.0049, 0., 0., 0.],
                [0.17, 0., 0., 0., 0., 0.0196, 0.8103, 0., 0., 0.],
                [0.1607, 0., 0., 0., 0., 0., 0., 0.8393, 0., 0.],
                [0., 0., 0., 0., 0., 0., 0., 0., 1.0000, 0.],
                [0.4773, 0., 0., 0.4773, 0., 0., 0., 0., 0., 0.0453]]),
            '21-25': np.array([
                [0.9581, 0.0001, 0.0011, 0.0024, 0.0081, 0.0184, 0.0108, 0.0006, 0., 0.0004],
                [0.4472, 0.5528, 0., 0., 0., 0., 0., 0., 0., 0.],
                [0.2376, 0., 0.7624, 0., 0., 0., 0., 0., 0., 0.],
                [0.1896, 0., 0.0094, 0.754, 0.0094, 0., 0.0188, 0., 0., 0.0188],
                [0.3715, 0.003, 0.003, 0., 0.5703, 0.0435, 0.0088, 0., 0., 0.],
                [0.3777, 0., 0.0036, 0.0036, 0.0258, 0.5835, 0.0036, 0.0024, 0., 0.],
                [0.137, 0., 0., 0.003, 0.0045, 0.0045, 0.848, 0.003, 0., 0.],
                [0.1079, 0., 0., 0., 0.0445, 0., 0.0225, 0.8251, 0., 0.],
                [0., 0., 0., 0., 0., 0., 0., 0., 1.0000, 0.],
                [0.3342, 0., 0., 0.1826, 0., 0., 0., 0., 0., 0.4831]]),
            '26-35': np.array([
                [0.9462, 0.0001, 0.0018, 0.0013, 0.0124, 0.0209, 0.0139, 0.003, 0.0001, 0.0002],
                [0.0939, 0.8581, 0., 0., 0., 0.048, 0., 0., 0., 0.],
                [0.1061, 0., 0.8762, 0.0051, 0.0025, 0.0025, 0.0051, 0.0025, 0., 0.],
                [0.1549, 0., 0., 0.8077, 0.0042, 0.0125, 0.0083, 0.0083, 0., 0.0042],
                [0.3031, 0.0016, 0.0021, 0.0021, 0.6589, 0.0211, 0.0053, 0.0053, 0., 0.0005],
                [0.2746, 0., 0.0028, 0.002, 0.0173, 0.691, 0.0073, 0.0048, 0., 0.0003],
                [0.1115, 0.0003, 0.0009, 0.0003, 0.0059, 0.0068, 0.8714, 0.0025, 0.0003, 0.],
                [0.0775, 0., 0.0015, 0., 0.0058, 0.0044, 0.0044, 0.905, 0., 0.0015],
                [0., 0., 0., 0., 0., 0., 0., 0., 1.0000, 0.],
                [0.1581, 0., 0.0121, 0., 0., 0., 0., 0., 0., 0.8297]]),
            '>35': np.array([
                [0.9462, 0.0001, 0.0018, 0.0013, 0.0124, 0.0209, 0.0139, 0.003, 0.0001, 0.0002],
                [0.0939, 0.8581, 0., 0., 0., 0.048, 0., 0., 0., 0.],
                [0.1061, 0., 0.8762, 0.0051, 0.0025, 0.0025, 0.0051, 0.0025, 0., 0.],
                [0.1549, 0., 0., 0.8077, 0.0042, 0.0125, 0.0083, 0.0083, 0., 0.0042],
                [0.3031, 0.0016, 0.0021, 0.0021, 0.6589, 0.0211, 0.0053, 0.0053, 0., 0.0005],
                [0.2746, 0., 0.0028, 0.002, 0.0173, 0.691, 0.0073, 0.0048, 0., 0.0003],
                [0.1115, 0.0003, 0.0009, 0.0003, 0.0059, 0.0068, 0.8714, 0.0025, 0.0003, 0.],
                [0.0775, 0., 0.0015, 0., 0.0058, 0.0044, 0.0044, 0.905, 0., 0.0015],
                [0., 0., 0., 0., 0., 0., 0., 0., 1.0000, 0.],
                [0.1581, 0., 0.0121, 0., 0., 0., 0., 0., 0., 0.8297]])
        },

        # Postpartum switching matrix, 1 to 6 months
        'pp1to6': {
            '<18': np.array([
                [0.9014, 0., 0.0063, 0.001, 0.0126, 0.051, 0.0272, 0.0005, 0., 0.],
                [0., 0.5, 0., 0., 0., 0., 0.5, 0., 0., 0.],
                [0., 0., 1.0000, 0., 0., 0., 0., 0., 0., 0.],
                [0., 0., 0., 1.0000, 0., 0., 0., 0., 0., 0.],
                [0.4, 0., 0., 0., 0.6, 0., 0., 0., 0., 0.],
                [0.0714, 0., 0., 0., 0., 0.9286, 0., 0., 0., 0.],
                [0., 0., 0., 0., 0., 0., 1.0000, 0., 0., 0.],
                [0., 0., 0., 0., 0., 0., 0., 1.0000, 0., 0.],
                [0., 0., 0., 0., 0., 0., 0., 0., 1.0000, 0.],
                [0., 0., 0., 0., 0., 0., 0., 0., 0., 1.0000]]),
            '18-20': np.array([
                [0.8775, 0.0007, 0.0026, 0.0033, 0.0191, 0.0586, 0.0329, 0.0046, 0., 0.0007],
                [0., 1.0000, 0., 0., 0., 0., 0., 0., 0., 0.],
                [0., 0., 1.0000, 0., 0., 0., 0., 0., 0., 0.],
                [0., 0., 0., 1.0000, 0., 0., 0., 0., 0., 0.],
                [0., 0., 0., 0., 0.75, 0.25, 0., 0., 0., 0.],
                [0.0278, 0., 0., 0., 0., 0.9722, 0., 0., 0., 0.],
                [0.0312, 0., 0., 0., 0., 0., 0.9688, 0., 0., 0.],
                [0., 0., 0., 0., 0., 0., 0., 1.0000, 0., 0.],
                [0., 0., 0., 0., 0., 0., 0., 0., 1.0000, 0.],
                [0., 0., 0., 0., 0., 0., 0., 0., 0., 1.0000]]),
            '21-25': np.array([
                [0.8538, 0.0004, 0.0055, 0.0037, 0.0279, 0.0721, 0.0343, 0.0022, 0., 0.],
                [0., 1.0000, 0., 0., 0., 0., 0., 0., 0., 0.],
                [0., 0., 0.9583, 0., 0., 0.0417, 0., 0., 0., 0.],
                [0., 0., 0., 0.5, 0.25, 0.25, 0., 0., 0., 0.],
                [0.0244, 0., 0., 0., 0.9512, 0.0244, 0., 0., 0., 0.],
                [0.0672, 0., 0., 0., 0., 0.9328, 0., 0., 0., 0.],
                [0.0247, 0., 0., 0., 0., 0.0123, 0.963, 0., 0., 0.],
                [0., 0., 0., 0., 0., 0., 0., 1.0000, 0., 0.],
                [0., 0., 0., 0., 0., 0., 0., 0., 1.0000, 0.],
                [0., 0., 0., 0., 0., 0., 0., 0., 0., 1.0000]]),
            '26-35': np.array([
                [0.8433, 0.0008, 0.0065, 0.004, 0.029, 0.0692, 0.039, 0.0071, 0.0001, 0.001],
                [0., 0.5, 0., 0., 0., 0., 0.5, 0., 0., 0.],
                [0.027, 0., 0.9189, 0., 0., 0.027, 0.027, 0., 0., 0.],
                [0.1667, 0., 0., 0.6667, 0., 0., 0.1667, 0., 0., 0.],
                [0.0673, 0., 0., 0., 0.8654, 0.0288, 0.0385, 0., 0., 0.],
                [0.0272, 0., 0.0039, 0., 0.0078, 0.9533, 0.0078, 0., 0., 0.],
                [0.0109, 0., 0., 0., 0.0036, 0., 0.9855, 0., 0., 0.],
                [0.0256, 0., 0., 0., 0., 0.0256, 0., 0.9487, 0., 0.],
                [0., 0., 0., 0., 0., 0., 0., 0., 1.0000, 0.],
                [0., 0., 0., 0., 0., 0., 0., 0., 0., 1.0000]]),
            '>35': np.array([
                [0.8433, 0.0008, 0.0065, 0.004, 0.029, 0.0692, 0.039, 0.0071, 0.0001, 0.001],
                [0., 0.5, 0., 0., 0., 0., 0.5, 0., 0., 0.],
                [0.027, 0., 0.9189, 0., 0., 0.027, 0.027, 0., 0., 0.],
                [0.1667, 0., 0., 0.6667, 0., 0., 0.1667, 0., 0., 0.],
                [0.0673, 0., 0., 0., 0.8654, 0.0288, 0.0385, 0., 0., 0.],
                [0.0272, 0., 0.0039, 0., 0.0078, 0.9533, 0.0078, 0., 0., 0.],
                [0.0109, 0., 0., 0., 0.0036, 0., 0.9855, 0., 0., 0.],
                [0.0256, 0., 0., 0., 0., 0.0256, 0., 0.9487, 0., 0.],
                [0., 0., 0., 0., 0., 0., 0., 0., 1.0000, 0.],
                [0., 0., 0., 0., 0., 0., 0., 0., 0., 1.0000]])
        },

        # Postpartum initiation vectors, 0 to 1 month
        'pp0to1': {
            '<18': np.array([0.9607, 0.0009, 0.0017, 0.0009, 0.0021, 0.0128, 0.0205, 0.0004, 0., 0.]),
            '18-20': np.array([0.9525, 0.0006, 0.0017, 0.0006, 0.0028, 0.0215, 0.0198, 0.0006, 0., 0.]),
            '21-25': np.array([0.9379, 0., 0.0053, 0.0009, 0.0083, 0.0285, 0.0177, 0.0013, 0., 0.]),
            '26-35': np.array([0.9254, 0.0002, 0.0036, 0.0007, 0.0102, 0.0265, 0.0268, 0.004, 0.0022, 0.0004]),
            '>35': np.array([0.9254, 0.0002, 0.0036, 0.0007, 0.0102, 0.0265, 0.0268, 0.004, 0.0022, 0.0004]),
        }
    }
    return raw
    '''

def method_probs():
    '''
    Define "raw" (un-normalized, un-trended) matrices to give transitional probabilities
    from PMA Kenya contraceptive calendar data.

    Probabilities in this function are annual probabilities of initiating (top row), discontinuing (first column),
    continuing (diagonal), or switching methods (all other entries).

    Probabilities at postpartum month 1 are 1 month transitional probabilities
    for starting a method after delivery.

    Probabilities at postpartum month 6 are 5 month transitional probabilities
    for starting or changing methods over the first 6 months postpartum.

    Data from Kenya PMA contraceptive calendars, 2019-2020
    Processed from matrices_kenya_pma_2019_20.csv using process_matrices.py
    '''

    raw = {

        # Main switching matrix: all non-postpartum women
        'annual': {
            '<18': np.array([
                [0.9578, 0.0003, 0.0023, 0.024 , 0.0025, 0.005 , 0.0043, 0.0002, 0.0002, 0.0035],
                [0.5684, 0.0179, 0.0038, 0.0752, 0.2552, 0.0295, 0.0024, 0.0001, 0.0001, 0.0475],
                [0.1187, 0.0001, 0.8034, 0.0471, 0.0173, 0.0021, 0.0003, 0.    , 0.    , 0.0111],
                [0.6347, 0.0006, 0.0016, 0.3171, 0.0078, 0.0131, 0.002 , 0.0001, 0.0001, 0.0229],
                [0.1704, 0.0001, 0.0006, 0.0162, 0.7059, 0.0896, 0.0038, 0.    , 0.    , 0.0135],
                [0.1791, 0.    , 0.0007, 0.0027, 0.0169, 0.7371, 0.0629, 0.    , 0.    , 0.0006],
                [0.1138, 0.    , 0.0144, 0.002 , 0.0006, 0.0302, 0.8386, 0.    , 0.    , 0.0004],
                [0.1352, 0.    , 0.0002, 0.0019, 0.0002, 0.0003, 0.0003, 0.8617, 0.    , 0.0003],
                [0.    , 0.    , 0.    , 0.    , 0.    , 0.    , 0.    , 0.    , 1.    , 0.    ],
                [0.7052, 0.0003, 0.0166, 0.1279, 0.0253, 0.0282, 0.0032, 0.0001, 0.0001, 0.0931]]),
            '18-20': np.array([
                [0.8392, 0.0014, 0.0132, 0.0705, 0.0131, 0.0331, 0.0199, 0.0003, 0.0001, 0.0091],
                [0.3917, 0.2362, 0.0072, 0.3268, 0.0115, 0.0138, 0.0093, 0.0001, 0.    , 0.0033],
                [0.1867, 0.0082, 0.6907, 0.0706, 0.0035, 0.0147, 0.0037, 0.    , 0.    , 0.0219],
                [0.4299, 0.0063, 0.0162, 0.4647, 0.0286, 0.0279, 0.0213, 0.0001, 0.    , 0.0049],
                [0.2567, 0.0005, 0.0031, 0.0339, 0.5704, 0.0974, 0.0262, 0.    , 0.    , 0.0117],
                [0.2396, 0.0002, 0.0047, 0.0134, 0.0189, 0.6235, 0.0971, 0.    , 0.    , 0.0025],
                [0.1203, 0.0001, 0.001 , 0.0057, 0.0246, 0.0458, 0.8005, 0.    , 0.    , 0.002 ],
                [0.    , 0.    , 0.    , 0.    , 0.    , 0.    , 0.    , 1.    , 0.    , 0.    ],
                [0.0612, 0.    , 0.0004, 0.0026, 0.0004, 0.0011, 0.0006, 0.    , 0.9332, 0.0004],
                [0.5869, 0.0079, 0.0513, 0.1252, 0.0303, 0.0183, 0.0228, 0.0001, 0.    , 0.1571]]),
            '21-25': np.array([
                [0.7658, 0.0054, 0.0157, 0.0507, 0.0161, 0.0809, 0.0427, 0.0026, 0.0003, 0.0198],
                [0.4475, 0.1729, 0.1476, 0.0282, 0.0091, 0.0755, 0.0965, 0.0009, 0.0001, 0.0219],
                [0.1748, 0.0125, 0.6072, 0.0684, 0.0151, 0.0648, 0.03  , 0.0004, 0.    , 0.0269],
                [0.3311, 0.011 , 0.0225, 0.5046, 0.0152, 0.0625, 0.0344, 0.0019, 0.0001, 0.0168],
                [0.2285, 0.0069, 0.0112, 0.0189, 0.5645, 0.1011, 0.0465, 0.0115, 0.    , 0.0108],
                [0.1962, 0.0019, 0.0063, 0.0099, 0.0263, 0.6879, 0.0656, 0.0005, 0.    , 0.0054],
                [0.1346, 0.0013, 0.0028, 0.0084, 0.0107, 0.0481, 0.7906, 0.0006, 0.    , 0.003 ],
                [0.1184, 0.0005, 0.0011, 0.0038, 0.0014, 0.0208, 0.0221, 0.83  , 0.    , 0.0019],
                [0.1765, 0.0007, 0.0016, 0.0057, 0.0017, 0.0085, 0.0043, 0.0003, 0.7981, 0.0028],
                [0.5085, 0.0085, 0.0829, 0.0964, 0.0422, 0.12  , 0.04  , 0.0015, 0.0001, 0.0999]]),
            '26-35': np.array([
                [0.7865, 0.0028, 0.0097, 0.0245, 0.0209, 0.0864, 0.0506, 0.0057, 0.0016, 0.0113],
                [0.1941, 0.5082, 0.0085, 0.0392, 0.0435, 0.0802, 0.1139, 0.0011, 0.0002, 0.011 ],
                [0.1255, 0.0019, 0.6694, 0.0287, 0.0362, 0.0787, 0.0313, 0.0108, 0.0002, 0.0172],
                [0.3772, 0.0169, 0.0177, 0.462 , 0.0312, 0.0451, 0.0171, 0.003 , 0.0005, 0.0294],
                [0.1759, 0.0024, 0.0081, 0.0102, 0.6488, 0.0881, 0.052 , 0.0076, 0.0002, 0.0068],
                [0.1732, 0.0022, 0.0081, 0.0087, 0.0257, 0.72  , 0.0565, 0.002 , 0.0004, 0.0031],
                [0.1008, 0.0019, 0.0025, 0.0021, 0.0075, 0.0383, 0.8418, 0.0026, 0.0001, 0.0024],
                [0.0852, 0.0034, 0.0059, 0.0015, 0.014 , 0.0097, 0.0227, 0.8567, 0.0001, 0.0008],
                [0.0304, 0.0001, 0.0003, 0.0009, 0.0004, 0.0019, 0.001 , 0.0001, 0.961 , 0.0042],
                [0.3847, 0.0026, 0.0276, 0.1025, 0.0153, 0.1219, 0.0486, 0.0019, 0.0063, 0.2886]]),
            '>35': np.array([
                [0.9082, 0.0012, 0.0024, 0.0207, 0.0116, 0.0343, 0.014 , 0.0007, 0.002 , 0.0049],
                [0.1334, 0.775 , 0.0004, 0.025 , 0.0015, 0.0366, 0.027 , 0.0002, 0.0002, 0.0007],
                [0.0334, 0.0026, 0.9284, 0.0049, 0.0056, 0.0204, 0.0011, 0.0011, 0.    , 0.0025],
                [0.2519, 0.0098, 0.0006, 0.6864, 0.0064, 0.0079, 0.0218, 0.0001, 0.0003, 0.0148],
                [0.1553, 0.0002, 0.0138, 0.0039, 0.7037, 0.0656, 0.0487, 0.0056, 0.0002, 0.003 ],
                [0.1269, 0.0013, 0.0111, 0.0047, 0.0218, 0.7748, 0.0499, 0.0044, 0.0017, 0.0033],
                [0.0765, 0.0022, 0.0044, 0.0033, 0.0148, 0.0389, 0.8536, 0.0019, 0.0012, 0.0032],
                [0.0605, 0.0001, 0.0013, 0.0007, 0.0006, 0.0126, 0.0063, 0.9143, 0.0001, 0.0034],
                [0.0061, 0.    , 0.    , 0.0001, 0.0001, 0.0002, 0.0027, 0.    , 0.9909, 0.    ],
                [0.2256, 0.0004, 0.0198, 0.0236, 0.038 , 0.0711, 0.0689, 0.0004, 0.0003, 0.5519]])
        },


        # Postpartum switching matrix, 1 to 6 months
        'pp1to6': {
            '<18': np.array([
                [0.7005, 0.    , 0.0054, 0.026 , 0.0172, 0.1096, 0.1413, 0.    ,0.    , 0.    ],
                [0.    , 1.    , 0.    , 0.    , 0.    , 0.    , 0.    , 0.    ,0.    , 0.    ],
                [0.    , 0.    , 1.    , 0.    , 0.    , 0.    , 0.    , 0.    ,0.    , 0.    ],
                [0.    , 0.    , 0.    , 1.    , 0.    , 0.    , 0.    , 0.    ,0.    , 0.    ],
                [0.    , 0.    , 0.    , 0.    , 0.6154, 0.3846, 0.    , 0.    ,0.    , 0.    ],
                [0.0913, 0.    , 0.    , 0.    , 0.    , 0.7858, 0.1229, 0.    ,0.    , 0.    ],
                [0.    , 0.    , 0.    , 0.    , 0.    , 0.    , 1.    , 0.    ,0.    , 0.    ],
                [0.    , 0.    , 0.    , 0.    , 0.    , 0.    , 0.    , 1.    ,0.    , 0.    ],
                [0.    , 0.    , 0.    , 0.    , 0.    , 0.    , 0.    , 0.    ,1.    , 0.    ],
                [0.    , 0.    , 0.    , 0.    , 0.    , 0.    , 0.    , 0.    ,0.    , 1.    ]]),
            '18-20': np.array([
                [0.565 , 0.    , 0.    , 0.0078, 0.0146, 0.2205, 0.192 , 0.    ,0.    , 0.    ],
                [0.    , 1.    , 0.    , 0.    , 0.    , 0.    , 0.    , 0.    ,0.    , 0.    ],
                [0.    , 0.    , 0.6788, 0.    , 0.    , 0.3212, 0.    , 0.    ,0.    , 0.    ],
                [0.    , 0.    , 0.    , 0.397 , 0.    , 0.603 , 0.    , 0.    ,0.    , 0.    ],
                [0.    , 0.    , 0.    , 0.    , 1.    , 0.    , 0.    , 0.    ,0.    , 0.    ],
                [0.    , 0.    , 0.    , 0.    , 0.    , 0.9237, 0.0763, 0.    ,0.    , 0.    ],
                [0.    , 0.    , 0.    , 0.    , 0.    , 0.    , 1.    , 0.    ,0.    , 0.    ],
                [0.    , 0.    , 0.    , 0.    , 0.    , 0.    , 0.    , 1.    ,0.    , 0.    ],
                [0.    , 0.    , 0.    , 0.    , 0.    , 0.    , 0.    , 0.    ,1.    , 0.    ],
                [0.    , 0.    , 0.    , 0.    , 0.    , 0.    , 0.    , 0.    ,0.    , 1.    ]]),
            '21-25': np.array([
                [0.4814, 0.0062, 0.0085, 0.0191, 0.0364, 0.2541, 0.1712, 0.0205, 0.    , 0.0025],
                [0.    , 1.    , 0.    , 0.    , 0.    , 0.    , 0.    , 0.    ,0.    , 0.    ],
                [0.    , 0.    , 0.6549, 0.    , 0.    , 0.3451, 0.    , 0.    ,0.    , 0.    ],
                [0.    , 0.    , 0.    , 0.5075, 0.    , 0.451 , 0.0415, 0.    ,0.    , 0.    ],
                [0.    , 0.    , 0.    , 0.    , 0.6087, 0.32  , 0.0713, 0.    ,0.    , 0.    ],
                [0.0329, 0.    , 0.    , 0.    , 0.    , 0.8558, 0.1014, 0.0098,0.    , 0.    ],
                [0.    , 0.    , 0.    , 0.    , 0.    , 0.    , 1.    , 0.    ,0.    , 0.    ],
                [0.    , 0.    , 0.    , 0.    , 0.    , 0.    , 0.    , 1.    ,0.    , 0.    ],
                [0.    , 0.    , 0.    , 0.    , 0.    , 0.    , 0.    , 0.    ,1.    , 0.    ],
                [0.    , 0.    , 0.    , 0.    , 0.    , 0.3303, 0.    , 0.    ,0.    , 0.6697]]),
            '26-35': np.array([
                [0.5309, 0.    , 0.0128, 0.0119, 0.0355, 0.2012, 0.1932, 0.0144,0.    , 0.    ],
                [0.    , 0.8094, 0.    , 0.    , 0.    , 0.1906, 0.    , 0.    ,0.    , 0.    ],
                [0.    , 0.    , 0.9214, 0.    , 0.    , 0.0786, 0.    , 0.    ,0.    , 0.    ],
                [0.096 , 0.    , 0.    , 0.8052, 0.    , 0.0704, 0.    , 0.    ,0.    , 0.0285],
                [0.    , 0.    , 0.    , 0.    , 0.7361, 0.1569, 0.107 , 0.    ,0.    , 0.    ],
                [0.0445, 0.    , 0.    , 0.    , 0.    , 0.9078, 0.035 , 0.    ,0.0127, 0.    ],
                [0.0063, 0.    , 0.    , 0.    , 0.0052, 0.014 , 0.9746, 0.    ,0.    , 0.    ],
                [0.    , 0.    , 0.    , 0.    , 0.    , 0.    , 0.    , 1.    ,0.    , 0.    ],
                [0.2318, 0.    , 0.    , 0.    , 0.    , 0.    , 0.    , 0.    ,0.7682, 0.    ],
                [0.    , 0.    , 0.    , 0.    , 0.    , 0.    , 0.    , 0.    ,0.    , 1.    ]]),
            '>35': np.array([
                [0.6572, 0.    , 0.0115, 0.0184, 0.0639, 0.1318, 0.1068, 0.0031,0.0047, 0.0025],
                [0.    , 1.    , 0.    , 0.    , 0.    , 0.    , 0.    , 0.    ,0.    , 0.    ],
                [0.    , 0.    , 1.    , 0.    , 0.    , 0.    , 0.    , 0.    ,0.    , 0.    ],
                [0.4391, 0.    , 0.    , 0.5609, 0.    , 0.    , 0.    , 0.    ,0.    , 0.    ],
                [0.    , 0.    , 0.    , 0.    , 1.    , 0.    , 0.    , 0.    ,0.    , 0.    ],
                [0.    , 0.    , 0.    , 0.    , 0.    , 1.    , 0.    , 0.    ,0.    , 0.    ],
                [0.0392, 0.    , 0.    , 0.    , 0.    , 0.    , 0.9608, 0.    ,0.    , 0.    ],
                [0.    , 0.    , 0.    , 0.    , 0.    , 0.    , 0.    , 1.    ,0.    , 0.    ],
                [0.    , 0.    , 0.    , 0.    , 0.    , 0.    , 0.    , 0.    ,1.    , 0.    ],
                [0.    , 0.    , 0.    , 0.    , 0.    , 0.    , 0.    , 0.    ,0.    , 1.    ]])
        },

        # Postpartum initiation vectors, 0 to 1 month
        'pp0to1': {
            '<18': np.array([0.801 , 0.    , 0.0052, 0.0099, 0.0089, 0.0508, 0.1243, 0.    ,0.    , 0.    ]),
            '18-20': np.array([0.7849, 0.    , 0.0066, 0.0134, 0.0082, 0.0793, 0.1007, 0.0038, 0.    , 0.0033]),
            '21-25': np.array([0.7252, 0.003 , 0.0104, 0.0151, 0.0108, 0.1242, 0.1068, 0.0015, 0.    , 0.0029]),
            '26-35': np.array([0.7706, 0.004 , 0.011 , 0.0121, 0.0142, 0.0835, 0.0829, 0.0095,0.0092, 0.0031]),
            '>35': np.array([0.8013, 0.    , 0.0037, 0.0093, 0.0059, 0.0594, 0.0622, 0.0075, 0.0406, 0.0101]),
        }
    }

    return raw


def barriers():
    ''' Reasons for nonuse -- taken from Kenya DHS 2014. '''

    barriers = sc.odict({
        'No need': 40.3,
        'Opposition': 22.7,
        'Knowledge': 3.5,
        'Access': 13.4,
        'Health': 32.5,
    })

    barriers[:] /= barriers[:].sum()  # Ensure it adds to 1
    return barriers


# %% Make and validate parameters

def make_pars():
    '''
    Take all parameters and construct into a dictionary
    '''

    # Scalar parameters and filenames
    pars = scalar_pars()
    pars['filenames'] = filenames()

    # Demographics and pregnancy outcome
    pars['age_pyramid'] = age_pyramid()
    pars['age_mortality'] = age_mortality()
    pars['maternal_mortality'] = maternal_mortality()
    pars['infant_mortality'] = infant_mortality()
    pars['miscarriage_rates'] = miscarriage()
    pars['stillbirth_rate'] = stillbirth()

    # Fecundity
    pars['age_fecundity'] = female_age_fecundity()
    pars['fecundity_ratio_nullip'] = fecundity_ratio_nullip()
    pars['lactational_amenorrhea'] = lactational_amenorrhea()

    # Pregnancy exposure
    pars['sexual_activity'] = sexual_activity()
    pars['sexual_activity_pp'] = sexual_activity_pp()
    pars['debut_age'] = debut_age()
    pars['exposure_age'] = exposure_age()
    pars['exposure_parity'] = exposure_parity()
    pars['spacing_pref'] = birth_spacing_pref()

    # Contraceptive methods
    pars['methods'] = methods()
    pars['methods']['raw'] = method_probs()
    pars['barriers'] = barriers()

    return pars
