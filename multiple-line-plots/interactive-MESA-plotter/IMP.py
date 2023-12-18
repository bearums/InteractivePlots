#TODO update documentation, test with different bokeh versions 
#     when reset button pressed, reset view position of plot 
# changelog - removed mesareader dependency
#           - added round_num option to round data. if round_num is 99, no rounding is done

import os,sys,glob
import numpy as np
import bokeh
from collections import OrderedDict
from bokeh.layouts import column, row
from bokeh.models import CustomJS, CheckboxGroup,CheckboxButtonGroup,RadioGroup,Select, Div, Button, LinearAxis
from bokeh.plotting import ColumnDataSource, figure, output_file, show, save
from bokeh.embed import components
from jinja2 import Template, Environment, BaseLoader
from itertools import cycle


class iMESAplotter:
    def __init__(self,directory,mode='single', history_file_name= 'history.data', history_files=None, round_num=99):
        self.mode= mode
        self.round_num = round_num
        if mode=='single':
            self.dir = directory
            self.history_files=glob.glob(os.path.join(self.dir,'**/%s'%history_file_name))
        elif mode=='binary':
            self.dir = directory
            self.history_files=glob.glob(os.path.join(self.dir,'**/%s'%history_file_name))
            self.binary_history = os.path.join(self.dir, 'binary_history.data')
        elif mode=='multiple' :
            self.history_files=[]
            for d in directory:
                self.history_files+=glob.glob(os.path.join(d,'**/%s'%history_file_name))
        elif history_files is not None:
            self.history_files= history_files
        self.html_template="""<!DOCTYPE html>
                                <html lang="en">
                                    <head>
                                    <!--  <style>
                                    .bk-root .bk-btn-default:nth-child(1){
                                    color: #ff0000;    
                                    }
                                    .bk-root .bk-btn-default:nth-child(2){
                                    color: #0000ff;    
                                    }
                                    </style>-->
                                        <meta charset="utf-8">
                                        <title>{{page_title}}</title>
                                    <script src="https://cdn.bokeh.org/bokeh/release/bokeh-{{bokeh_version}}.min.js"
                                        crossorigin="anonymous"></script>
                                    <script src="https://cdn.bokeh.org/bokeh/release/bokeh-widgets-{{bokeh_version}}.min.js"
                                        crossorigin="anonymous"></script>
                                        {{script}}
                                    </head>
                                    <body>
                                        {{divs}}
                                    <hr width="80%" align="center">
                                    <br>
                                    <p>{{text}}</p>
                                    </body>
                                </html> """
        self.template= Environment(loader=BaseLoader()).from_string(self.html_template)

    def load_html_template(self,file):
        """loads a custom html template from file"""
        with open(file) as f:
            self.template = Template(f.read())
        
    def load_data(self,file, qual_list=None,x_qual=None, y_qual=None):
        """loads data from MESA log file into Bokeh Column DataSource object. 
            also gets column names and sets data to display"""
        bulk_names_line = 6
        header_names_line = 2
        bulk_data = np.genfromtxt( file, skip_header=bulk_names_line - 1, names=True, dtype=None)
        bulk_names = bulk_data.dtype.names
        header_data = []
        with open(file) as f:
            for i, line in enumerate(f):
                if i == header_names_line - 1:
                    header_names = line.split()
                elif i == header_names_line:
                    header_data = [eval(datum) for datum in line.split()]
                elif i > header_names_line:
                    break
        header_data = dict(zip(header_names, header_data))

       
        if qual_list is None:
            qual_list = list(bulk_names)
            
            
        # round data to make smaller output file
        frmt_str = '{:0.%se}'%self.round_num
        dat_dict=OrderedDict()
        for q in qual_list:
            if self.round_num != 99:
                data_rounded = [float(frmt_str.format(p)) for p in bulk_data[q]]
                dat_dict[q] =data_rounded
            else:
                dat_dict[q] = bulk_data[q]


        if x_qual is None:
            x_qual=qual_list[0]
        if y_qual is None:
            y_qual=qual_list[1]
            
        source = ColumnDataSource(dat_dict )
        return [source, qual_list, x_qual, y_qual, header_data]
    
    def load_history_files(self, qual_list=None,x_qual=None, y_qual=None):
        datas=[]
        for h in self.history_files:
            dat = self.load_data(h, qual_list, x_qual,y_qual)
            datas.append(dat)
            
        source_list=[x[0] for x in datas]
        qual_lists = [x[1] for x in datas]
        x_quals=[x[2] for x in datas]
        y_quals=[x[3] for x in datas]
        
        if not all(l ==qual_lists[0] for l in qual_lists):# if lists are not the same
            #get common elements in lists
            qual_list= sorted(list(set.intersection(*[set(l) for l in qual_lists])))
        else: qual_list=qual_lists[0]
        
        if x_qual is None:
            if  all(l ==x_quals[0] for l in x_quals):# if all x_quals are same
                x_qual= x_quals[0]
            else:
                x_qual = qual_list[0]
                
        if y_qual is None:
            if  all(l ==y_quals[0] for l in y_quals):# if all x_quals are same
                y_qual= y_quals[0]
            else:
                y_qual = qual_list[1]
                
        #check that desired x and y quantities are in history files
        if not all(x_qual in sublist for sublist in qual_lists):
            print('Setting x quantity to %s!'%qual_list[0])
            x_qual=qual_list[0]
        if not all(y_qual in sublist for sublist in qual_lists):
            print('Setting y quantity to %s!'%qual_list[1])
            y_qual=qual_list[1]
        for s in source_list:
            s.data['x_data'] = s.data[x_qual]
            s.data['y_data']=s.data[y_qual]
        return [source_list, qual_list,x_qual, y_qual]
    
    def make_plot(self, plot_width=800,plot_height=600,line_cols=['black','red','blue','green','orange'], 
                  qual_list=None, x_qual=None, y_qual=None, verbose=False):
            
        if verbose:
            print('Loading history files: %s'%(self.history_files))
            
        loaded_history_files= self.load_history_files(qual_list=qual_list,x_qual=x_qual, y_qual=y_qual)
        
        source_list= loaded_history_files[0]
        
        qual_list = loaded_history_files[1]
        x_qual = loaded_history_files[2]
        y_qual= loaded_history_files[3]
       
        TOOLTIPS = [("(x,y)", "($x, $y)")]
        fig = figure(  plot_width=plot_width, plot_height=plot_height, 
                      x_axis_label=x_qual, y_axis_label=y_qual, tooltips=TOOLTIPS, name='plot')
        # format the plot a bit
        fig.xgrid.visible = False
        fig.ygrid.visible = False
        fig.add_layout(LinearAxis(major_label_text_color=None), 'right')
        fig.add_layout(LinearAxis(major_label_text_color=None), 'above')
        #ticks_top=plot.add_layout(LinearAxis(major_label_text_color=None), 'above')
        fig.axis.major_tick_out = 0
        fig.axis.minor_tick_out = 0
        fig.axis.major_tick_in = 5
        fig.axis.minor_tick_in = 2
        
        #flip x-axis for HRD
        if x_qual=='log_Teff' and y_qual=='log_L':
            fig.x_range.flipped = True
        
        
        lines=[]
        markers=[]
        col_cycle = cycle(line_cols)
        
        for s,i in zip(source_list, range(1, len(source_list)+1)):
            col=next(col_cycle)
            if self.mode=='single':
                lines.append(fig.line('x_data','y_data', source=s, line_width=2.,
                                       line_color=col ))
            else:
                lines.append(fig.line('x_data','y_data', source=s, line_width=2.,
                                       line_color=col,legend_label='star%s'%i ))
            markers.append(fig.scatter(x="x_data", y="y_data",source=s, line_color= col, marker="x", size=12,visible=False))
        
        #set up selectors for x and y quantities 
        select_x_value = Select(title="x-quantity", value=x_qual, options=qual_list, width=120, name='x_data_selector')
        select_y_value = Select(title="y-quantity", value=y_qual, options=qual_list, width=120, name='y_data_selector')
        x_scale_radiogroup = RadioGroup(labels=['x-scale linear','x-scale abs(log)', 'x-scale 10^'], active=0, name='x_scale_setter')
        y_scale_radiogroup = RadioGroup(labels=['y-scale linear','y-scale abs(log)', 'y-scale 10^'], active=0, name='y_scale_setter')
        
        #scale switching buttons
        x_scale_radiogroup.js_on_click(CustomJS(
            args=dict( source_list=source_list, ax1=fig.xaxis,x_select = select_x_value),
        code="""
        const s = cb_obj.active;
        var x_val=x_select.value;
        var l;
        if (s==1){
        
        ax1[1].axis_label = 'log('+x_val +')';
        console.log('changing x data to log' + ax1[0].axis_label);
        for (l of source_list){
            const data = l.data;
            const x_data = data['x_data'];
            for (var i = 0; i < x_data.length; i++) {
                x_data[i]= Math.log10(Math.abs(data[x_val][i]));}
            l.change.emit();}
        }          
        if (s==0){
        ax1[1].axis_label = x_val ;
        console.log('changing x data to linear' + s);
        for (l of source_list){
            const data = l.data;
            const x_data = data['x_data'];
            for (var i = 0; i < x_data.length; i++) {
                x_data[i]= data[x_val][i];}
            l.change.emit();}
        }
        if (s==2){
        ax1[1].axis_label = '10^'+x_val ;
        console.log('changing x data to 10^' + s);
        for (l of source_list){
            const data = l.data;
            const x_data = data['x_data'];
            for (var i = 0; i < x_data.length; i++) {
                x_data[i]= 10**(data[x_val][i]);}
            l.change.emit();}
        }
        """))
        y_scale_radiogroup.js_on_click(CustomJS(args=dict( source_list=source_list, ax1=fig.yaxis,y_select = select_y_value),
        code="""
        const s = cb_obj.active;
        var y_val=y_select.value;
        var l;
        if (s==1){
        
        ax1[0].axis_label = 'log('+y_val +')';
        console.log('changing y data to log' + ax1[0].axis_label);
        for (l of source_list){
            const data = l.data;
            const y_data = data['y_data'];
            for (var i = 0; i < y_data.length; i++) {
                y_data[i]= Math.log10(Math.abs(data[y_val][i]));}
            l.change.emit();}
        }
        if (s==0){
        ax1[0].axis_label = y_val ;
        console.log('changing y data to linear' + s);
        for (l of source_list){
            const data = l.data;
            const y_data = data['y_data'];
            for (var i = 0; i < y_data.length; i++) {
                y_data[i]= data[y_val][i];}
            l.change.emit();}
        }
        if (s==2){
        ax1[0].axis_label = '10^'+y_val ;
        console.log('changing y data to 10^' + s);
        for (l of source_list){
            const data = l.data;
            const y_data = data['y_data'];
            for (var i = 0; i < y_data.length; i++) {
                y_data[i]= 10**(data[y_val][i]);}
            l.change.emit();}
        }
        """))
        
        x_val_callback=CustomJS(args=dict(source_list=source_list, ax1=fig.xaxis, plot=fig, y_select=select_y_value,x_scale =x_scale_radiogroup ),
        code="""
        x_scale.active=0;
        if (y_select.value == 'log_L' && cb_obj.value=='log_Teff'){
            plot.x_range.flipped = true;
        }else{
            plot.x_range.flipped = false;}
        var x_new = cb_obj.value;
        console.log('ax1:' + ax1)
        ax1[1].axis_label = x_new;
        var l;
        for (l of source_list){
            const data = l.data;
            const x_data = data['x_data'];
            for (var i = 0; i < x_data.length; i++) {
            x_data[i]=data[x_new][i];
            }
            l.change.emit();
        }
        """)
        y_val_callback=CustomJS(args=dict(source_list=source_list, ax1=fig.yaxis, plot=fig, x_select = select_x_value, y_scale =y_scale_radiogroup ),
        code="""
        y_scale.active=0;
        if (x_select.value == 'log_Teff' && cb_obj.value=='log_L'){
            plot.x_range.flipped = true;
        }else{
            plot.x_range.flipped = false;}
        var y_new = cb_obj.value;
        console.log('ax1:' + ax1)
        ax1[0].axis_label = y_new;
        var l;
        for (l of source_list){
            const data = l.data;
            const y_data = data['y_data'];
            for (var i = 0; i < y_data.length; i++) {
                y_data[i]=data[y_new][i];}
            l.change.emit();
        }
        """)
        select_x_value.js_on_change('value', x_val_callback)
        select_y_value.js_on_change('value', y_val_callback)
        
        
        #set up reset button
        reset_button= Button(label='Reset', height=40, width=80, name='reset_button')
        reset_call = CustomJS(args=dict(lines=lines, source_list=source_list,p=fig,x_select = select_x_value,                 y_select=select_y_value,x_qual=x_qual, 
        y_qual=y_qual,x_scale =x_scale_radiogroup,y_scale =y_scale_radiogroup ,axy=fig.yaxis,axx=fig.xaxis ),
           code="""
        y_scale.active=0;
        x_scale.active=0;
        axy[0].axis_label = y_qual ;
        axx[1].axis_label = x_qual ;
        var l;
        for (l of source_list){
            const data = l.data;
            const x_data = data['x_data'];
            for (var i = 0; i < x_data.length; i++) {
                x_data[i]= data[x_qual][i];}
            const y_data = data['y_data'];
            for (var i = 0; i < y_data.length; i++) {
                y_data[i]= data[y_qual][i];}
            l.change.emit();}
        x_select.value = x_qual;
        y_select.value = y_qual;
        
        lines[0].visible=true;
        lines[1].visible=true;
        p.reset.emit();
        """)
        reset_button.js_on_click( reset_call)
         #set up show/hide markers button 
        marker_button= CheckboxButtonGroup(labels=['Show markers'], active=[], height=40, width=80, name='show_marker_box')
        marker_call = CustomJS(args=dict(markers=markers,lines=lines,p=fig),
           code="""
        for (var i = 0; i < lines.length; i++) {
        const m = markers[i]
        const l = lines[i]
         if (cb_obj.active.length>0 && l.visible) {
                m.visible=true;}
            else{m.visible=false;}
            m.change.emit();}
        """)
        marker_button.js_on_click( marker_call)
        if self.mode=='binary':
            #buttons for hiding star 1 & 2 
            js_code="""
            const s = cb_obj.active;
            console.log(marker_button.active);
            if (s.includes(0)){
            line.visible=true;
             if (marker_button.active.includes(0)) {marks.visible=true;}
            }
            else{
            line.visible=false;
            marks.visible=false;
            }
            """
            show_1_box = CheckboxButtonGroup(labels=['show Star 1'], active=[0], width=40 )
            show_1_box_callback = CustomJS(args=dict( line=lines[0], marks=markers[0],
                                                     marker_button=marker_button),
            code=js_code)

            show_2_box = CheckboxButtonGroup(labels=['show Star 2'], active=[0], width=40 )
            show_2_box_callback = CustomJS(args=dict( line=lines[1], marks=markers[1],
                                                    marker_button=marker_button),
            code=js_code)
            show_1_box.js_on_change('active',show_1_box_callback)
            show_2_box.js_on_change('active',show_2_box_callback)
            layout =  row(column(select_x_value,select_y_value,
                                 show_1_box, show_2_box,
                                 reset_button,marker_button,
                                 x_scale_radiogroup, y_scale_radiogroup, name='widgets'),column(fig, name='plot'))

        else:
            layout =  row(column( select_x_value,select_y_value, 
                                 reset_button,marker_button,
                                 x_scale_radiogroup, y_scale_radiogroup, name='widgets'),column(fig, name='plot'))
        self.figure=fig
        self.layout=layout
        self.lines= lines
        self.markers=markers
        self.widgets = [select_x_value,select_y_value, 
                                 reset_button,marker_button,
                                 x_scale_radiogroup, y_scale_radiogroup]
        script, div = components(self.layout)
        
        txt=''
        if self.mode=='binary':
            #check for binary_history.data file, if exsists get initial binary params
            if os.path.isfile(os.path.join(self.dir, 'binary_history.data')):
                header_data= self.load_data(os.path.join(self.dir, 'binary_history.data'))[4]
                M1i = round(header_data['initial_don_mass'],2)
                M2i=round(header_data['initial_acc_mass'],2)
                if M1i==0:
                    qi=0
                else:
                    qi= round(M2i/M1i,2)
                logPi = round(np.log10(header_data['initial_period_days']),3)
                txt+= """<p> <math> M<sub>1,i</sub>= %.3f M<sub>&#9737</sub></math> , <math>q<sub>i</sub>=%.3f </math> , <math>log<sub>10</sub>(P<sub>i</sub>/days)= %.3f</math> </p>"""%(M1i, qi, logPi)
            txt+="""\n<p>Plot generated from directory %s</p>"""%(self.dir)
        elif self.mode == 'multiple':
            for f,i in zip(self.history_files, range(1,len(self.history_files)+1)):
                txt+="""<p>Star%s generated from directory %s</p>\n"""%(i,f)
        elif self.mode=='single':
            txt+= """<p>Plot generated from directory %s</p>"""%(self.dir)
            
            
        self.text = txt
        
            
    def show_plot(self):
        show(self.layout)

    def save_plot(self, page_name='Plot.html', page_title='MESA Model'):
        script, div = components(self.layout)

        page=self.template.render(page_title=page_title,script=script, divs=div, bokeh_version=bokeh.__version__, 
                     text=self.text)
        
        with open( page_name, 'w') as f:
                f.write(page)
