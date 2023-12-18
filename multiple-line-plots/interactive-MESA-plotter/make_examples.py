#!/usr/bin/python3
from IMP import iMESAplotter
import os
os.system('mkdir -p examples')

import bokeh
print('bokeh version ', bokeh.__version__)

#single example
model_dir= 'models/single/10/'
mp=iMESAplotter(model_dir,mode='single')        
mp.make_plot(verbose=True, x_qual='log_Teff', y_qual='log_L')
mp.save_plot(page_name='examples/Plot_single.html')

#multiple example 
import glob
model_dirs = sorted(glob.glob('models/single/**'))
mp=iMESAplotter(model_dirs,mode='multiple')        
mp.make_plot(verbose=True, x_qual='log_Teff', y_qual='log_L')
mp.save_plot(page_name='examples/Plot_multiple.html')

#binary example
model_dir = 'models/binary/'
mp=iMESAplotter(model_dir,mode='binary')        
mp.make_plot(verbose=True, x_qual='log_Teff', y_qual='log_L')
mp.save_plot(page_name='examples/Plot_binary.html')

