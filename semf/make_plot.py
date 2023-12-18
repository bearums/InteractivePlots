#!/usr/bin/env python3

#################################
# This script produces an interactive plot to explore the semi-empirical mass formula through varying the constants in the formula
##################################
import numpy as np

from bokeh.io import curdoc
from bokeh.layouts import column, row
from bokeh.models import ColumnDataSource, Slider,  Button , ColorBar, LinearColorMapper
from bokeh.plotting import figure
from bokeh.models import CustomJS, Slider, CheckboxGroup, Div, Select, Button, LinearAxis, Label
from bokeh.plotting import ColumnDataSource, figure, output_file, save

# Set up data
aV0=15.8
aS0=18.3
aC0=0.7
aA0=23.2
aP0=12
kP0=0.5
value_list=[ aV0, aS0, aC0, aA0, aP0, kP0]
def binding_E(Z,N, aV=aV0, aS=aS0, aC=aC0, aA=aA0, aP=aP0, kP=kP0):
    A=Z+N
    
    q=aV* A
    w=- aS*A**(2/3.0)
    e=- aC* (Z*(Z-1))* A**(-1/3.0)
    r= - aA *(A- 2*Z)**2 /A
    
    Zint= (np.rint(Z)).astype(int)
    Nint= (np.rint(N)).astype(int)
    
    sgn = np.zeros(Zint.shape)
    sgn[(Zint%2==0) & (Nint%2==0)] = +1
    sgn[(Zint%2!=0) & (Nint%2!=0)] = -1
    t= sgn * aP*A**-float(kP)
    
    return (q+w+e+r+t)/A



x= np.arange(1,101,1)
y= np.arange(1,101,1)
X, Y = np.meshgrid(x, y)
E0= binding_E(N=X,Z=Y)
E0[E0<0] = 0

source0 = ColumnDataSource({'image': [E0], 'x0':[x[0]], 'y0':[y[0]], 'dw':[x[-1]],'dh':[y[-1]] })

source = ColumnDataSource({'image': [E0], 'x0':[x[0]], 'y0':[y[0]], 'dw':[x[-1]],'dh':[y[-1]] })

# Set up plot
p = figure(y_range=(y[0],y[-1]), x_range=(x[0],x[-1]), plot_width=800, plot_height=550,
           tooltips=[("x", "$x"), ("y", "$y"), ("value", "@image")], toolbar_location=None, tools=['reset'])
p.xgrid.visible = False
p.ygrid.visible = False
p.xaxis.axis_label= 'N= neutron number'
p.yaxis.axis_label= 'Z= proton number'
p.yaxis.axis_label_text_font_style = "bold"
p.xaxis.axis_label_text_font_style = "bold"
p.add_layout(LinearAxis(major_label_text_color=None), 'right')
p.add_layout(LinearAxis(major_label_text_color=None), 'above')

color_mapper = LinearColorMapper(palette="Viridis256", low=0, high=12.1)
p.image(image='image', x='x0', y='y0',  dw='dw', dh='dh', source=source,color_mapper=color_mapper) #palette='Viridis256'
#p.image(image=[E], x=x[0], y=y[0], dw=[100], dh=[100], palette='Viridis256')
p.line(x,y,  visible=True,line_width=2., line_color='white')

# Set up widgets
reset_button= Button(label='Reset', height=40, width=150)
calc_button= Button(label='Calculate', height=40, width=150)
av_slider = Slider(title="Volume constant/MeV", value=aV0, start=0, end=50, step=1)
as_slider = Slider(title="Surface constant/MeV", value=aS0, start=0, end=50, step=1)
ac_slider = Slider(title="Coulomb constant/MeV", value=aC0, start=0.0, end=5, step=0.1)
aa_slider = Slider(title="Asymmetry constant/MeV", value=aA0, start=0, end=50, step=1)
ap_slider = Slider(title="Pairing energy constant/MeV", value=aP0, start=0, end=50, step=1)
kp_slider = Slider(title="Pairing energy exponent", value=kP0, start=0, end=2, step=0.1)
slider_list=[av_slider, as_slider, ac_slider, aa_slider,ap_slider, kp_slider]

# Set up callbacks

#callback for reset button. sets all sliders to original values and resets binding energies 
reset_call = CustomJS(args=dict(source=source, slider_list=slider_list,value_list=value_list, E0=E0, source0=source0),
                    code="""
                            const data= source.data;
                            const E = data['image'];
                            const N_max = data['dw'];
                            const Z_max = data['dh'];

                            for (var N = 0; N < value_list.length; N++) {
                            slider_list[N].value= value_list[N]}
                            const av_i = value_list[0];
                            const as_i = value_list[1];
                            const ac_i = value_list[2];
                            const aa_i = value_list[3];
                            const ap_i = value_list[4];
                            const kp_i = value_list[5];
                            for (var N = 0; N < N_max; N++) {
                                for (var Z = 0; Z < Z_max; Z++) {
                                const A= N+Z;
                                var sgn = 0;
                                if ((N % 2 == 0) && (Z % 2 == 0)){
                                    sgn = 1;}
                                if ((N % 2 != 0) && (Z % 2 != 0)){
                                    sgn = -1;}
                                const e_val = Math.max(0 , (av_i * A - as_i *A **(2/3.0) - ac_i* (Z*(Z-1))* A**(-1/3.0) -  aa_i *(A- 2*Z)**2 /A + sgn * ap_i*A**(-kp_i))/ A);
                                E[0][Z*N_max + N] = e_val;
                                }
                            }
                            source.change.emit();
""")
reset_button.js_on_click( reset_call)


#callback for calculate button. reads the values of all sliders and recalculates binding energies 
calc_call = CustomJS(args=dict(source=source, slider_list=slider_list),
                    code="""
                            const data= source.data;
                            const E = data['image'];
                            const N_max = data['dw'];
                            const Z_max = data['dh'];

                            console.log('######');
                            const av_i = slider_list[0].value;
                            const as_i = slider_list[1].value;
                            const ac_i = slider_list[2].value;
                            const aa_i = slider_list[3].value;
                            const ap_i = slider_list[4].value;
                            const kp_i = slider_list[5].value;

                            for (var N = 0; N< N_max; N++) {
                                for (var Z = 0; Z < Z_max; Z++) {
                                const A= N+Z;
                                var sgn = 0;
                                if ((N % 2 == 0) && (Z % 2 == 0)){
                                    sgn = 1;}
                                if ((N % 2 != 0) && (Z % 2 != 0)){
                                    sgn = -1;}
                                const e_val = Math.max(0 , (av_i * A - as_i *A **(2/3.0) - ac_i* (Z*(Z-1))* A**(-1/3.0) -  aa_i *(A- 2*Z)**2 /A + sgn * ap_i*A**(-kp_i))/ A);
                                E[0][Z*N_max + N] = e_val;
                                }
                            }
                            source.change.emit();
                            """)
calc_button.js_on_click( calc_call)



#add colour bar
color_bar_height = 550 + 0
color_bar_width = 120
color_bar = ColorBar(color_mapper=color_mapper, 
                     label_standoff=12, border_line_color=None, location=(0,0))
color_bar_plot = figure(title="Binding energy per nucleon/MeV", title_location="right", 
                        height=color_bar_height, width=color_bar_width, 
                        toolbar_location=None, min_border=0, 
                        outline_line_color=None)
color_bar_plot.add_layout(color_bar, 'right')
color_bar_plot.title.align="center"
color_bar_plot.title.text_font_size = '12pt'

# Set up layouts 
inputs = column(row(calc_button,reset_button), av_slider, as_slider, ac_slider, aa_slider, ap_slider, kp_slider)
layout = row(inputs, p,color_bar_plot,  width=800)

print("saving file")
output_file("SEMF.html", title="SEMF")
save(layout)


