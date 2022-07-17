import plotly.graph_objects as go

def plotly_plot_bivariate_normal_pdf(x, y, z, name=""):
    fig = go.Figure(data=[go.Surface(x=y, y=x, z=z)])
    fig.update_traces(contours_z=dict(show=True, 
                                      usecolormap=True,
                                      highlightcolor="limegreen", 
                                      project_z=True))
    fig.update_layout(title=name, autosize=False,
                      scene_camera_eye=dict(x=1.5, y=-1.5, z=1.5),
                      width=1200, height=600,
                      margin=dict(l=50, r=50, b=50, t=50))
    fig.show()