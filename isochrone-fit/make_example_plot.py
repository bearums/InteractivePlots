
#!/usr/bin/env python3

#######################3
#makes an interactive bokeh plot to fit a sine curve to randomly generated data
############################
import numpy as np
import pandas as pd
from collections import OrderedDict
from bokeh.layouts import column, row
from bokeh.models import CustomJS, Slider, CheckboxGroup,CheckboxButtonGroup, Div, Select, Button, LinearAxis, Label
from bokeh.plotting import ColumnDataSource, figure, output_file, show



#generate noisy sine curve 
rng = np.random.default_rng()

A= 4.5 #10*rng.random()
T=  2.3 #5*rng.random()
x_offset = 10*rng.random()
y_offset = 10*rng.random()

x0 = np.linspace(0,1,200)
y0 = A* np.sin(x0*T*(2*np.pi))

y_noise = 0.4 * rng.normal(size=x0.size)
x_noise = 0.02 * rng.normal(size=x0.size)

y_data= y0 + y_noise
x_data = x0 + x_noise

y_data = y_data+ y_offset
x_data= x_data+ x_offset

# generate sine curves 
# lists of values must be strings to work with widgets 
amplitude_list = ['2','4','6','8','10']
period_list = ['1','2','3','4','5']
source_dict={}
#create a dictionary of dictinaries.First key is amplitude value. then dictionary with keys of period value
for a in amplitude_list:
    source_list=OrderedDict()
    for p in period_list:
        xx=np.linspace(0,1,100)
        yy = float(a) * np.sin(xx*float(p)*(2*np.pi))
        df=pd.DataFrame({'x_':xx, 'y_':yy,'x_plot':xx, 'y_plot':yy})
        source = ColumnDataSource(df[['y_','x_','y_plot','x_plot']])
        source_list[p]=source
    source_dict[a]= source_list

#build plot
a_init=amplitude_list[2]
p_init = period_list[0]
x_i= 0
y_i= 0

plot = figure(y_range=(1.02*y_data.min(),1.02*y_data.max()), x_range=(0,1.05*x_data.max()), plot_width=600, plot_height=420,   sizing_mode="scale_both")
plot.xgrid.visible = False
plot.ygrid.visible = False
plot.title.text = 'A dummy fitter'
plot.title.align = "center"
plot.title.text_color = "black"
plot.title.text_font_size = "20px"

# plot all lines, setting some to visible and some to invisible
lines={}
for a in source_dict.keys():
    lines_list=[]
    for p in source_dict[a].keys():
        s= source_dict[a][p]
        if a==a_init and p == p_init: 
            vis = True
        else:
            vis = False
        l = plot.line('x_plot','y_plot', source=s, visible=vis,line_width=2., line_color='green')
        l.tags=[p]              
        lines_list.append(l)
        lines[a]=lines_list


# define widgets 
x_slider = Slider(start=0., end=10, value=x_i, step=0.25, title="x offset",width=plot.plot_width, sizing_mode="scale_width",format="0[.]0000", bar_color='khaki')
y_slider = Slider(start=0., end=10, value=y_i, step=1.0, title="y offset",width=plot.plot_width, sizing_mode="scale_width", bar_color='khaki')
select_menu = Select(title="Amplitude", value=a_init, options=amplitude_list, width=80)
reset_button= Button(label='Reset', height=40, width=80)
show_obs_box = CheckboxButtonGroup(labels=['show obs.'], active=[0], width=40 )
checkbox = CheckboxGroup(labels=period_list, active=[period_list.index(p_init)], width=50 )
checkbox_label=Div(text='period', width= 50)

#setup callbacks 

#for selecting different periods
checkbox_callback = CustomJS(args=dict( select_menu=select_menu,lines=lines, value_list=amplitude_list, checkbox=checkbox),
                              code="""
    const t_new= select_menu.value;
    var a;
    var i;
    for (a of value_list){
        const l=lines[a];
        if (a==t_new){
            for ( i =0; i < l.length; i++){
                if (checkbox.active.includes(i)){
                    l[i].visible = true;}
                else{
                    l[i].visible = false;}
            }
        }
        else{
            for ( i =0; i < l.length; i++){
                l[i].visible = false;
            }
        }
    }
    """)

#for changing x and y offsets 
callback_slider = CustomJS(args=dict(source_dict=source_dict,
                              select_value_list=amplitude_list, slider1=x_slider, slider2= y_slider),
                    code="""
    const slider1_val = slider1.value;
    const slider2_val = slider2.value;
    var t;
    var a;
    for (a of select_value_list){
        const line_to_plot = source_dict[a];
        var v;
        for (v in line_to_plot){
            const s = line_to_plot[v];
            const data = s.data;
            const xx =data['x_plot'];
            const yy = data['y_plot'];
            for (var i = 0; i < xx.length; i++) {
                xx[i]=data['x_'][i] + slider1_val ; 
                yy[i]=data['y_'][i] + slider2_val ;
            }
            s.change.emit();
        }
    }
    """)


# for selecting different amplitudes
select_menu_callback= CustomJS(args=dict(source_dict=source_dict, lines=lines,
                                         select_menu=select_menu, select_value_list=amplitude_list,
                                         checkbox=checkbox),
                            code="""
    const t_new= select_menu.value;
    var a;
    const v_i= select_value_list;
    for (a of v_i){
        const s = lines[a];
        for ( i =0; i < s.length; i++){
            s[i].visible = false;
        }
    }
    
    const lines_active= lines[t_new];
    var i;
    for ( i =0; i < lines_active.length; i++){
        if (checkbox.active.includes(i)){
            lines_active[i].visible = true;}
        else{
            lines_active[i].visible = false;}
    }
    """)

# for resetting plot 
reset_call = CustomJS(args=dict(p=plot,s1=x_slider, s2= y_slider, x_val=x_i,y_val=y_i, 
checkbox=checkbox, initial_checkbox= period_list.index(p_init), lines=lines, 
                                select_menu=select_menu, select_val=a_init, select_value_list=amplitude_list ),
                    code="""
        var a;
        var i;
        for (a of select_value_list){  
            for ( i =0; i < lines[a].length; i++){
                lines[a][i].visible = false;}
        }
        checkbox.active=[initial_checkbox];
        select_menu.value= select_val;
        lines[select_val][initial_checkbox].visible = true;
        s2.value = y_val;
        s1.value = x_val;
        p.reset.emit();
        """)

#assign callbacks
checkbox.js_on_click(checkbox_callback)
x_slider.js_on_change('value', callback_slider)
y_slider.js_on_change('value', callback_slider)
select_menu.js_on_change('value', select_menu_callback)
reset_button.js_on_click( reset_call)


#plot observations 
obs=plot.circle(x_data, y_data, color="black", level= 'underlay',size=1.5)
show_obs_box = CheckboxButtonGroup(labels=['show obs.'], active=[0], width=40 )
show_obs_callback = CustomJS(args=dict( obs_points=obs),
                              code="""     
                    const s = cb_obj.active;
                    console.log('show obs' + s);
                    if (s.includes(0)){obs_points.visible=true;}
                    else{obs_points.visible=false;}""")

show_obs_box.js_on_click( show_obs_callback)


layout =  row( column(select_menu, checkbox_label, checkbox, reset_button,show_obs_box),  
              column(plot, row(column(x_slider, y_slider)),
                     sizing_mode="scale_both"),sizing_mode="scale_both")
show(layout)


