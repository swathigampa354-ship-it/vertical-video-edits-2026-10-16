"""Reviewed job-extension example, not mandatory content for unrelated speech.
Copy/adapt it into a new job only when its connected-nodes meaning fits the source.
Pass --scene-module /path/to/job_film.py. All actual text uses the base recorder.
"""
from PIL import ImageDraw
from edit import Film as PortableFilm,W,H,ease

class Film(PortableFilm):
    def scene(self,scene,raw,t,records):
        im=super().scene(scene,raw,t,records)
        if scene.get('custom')!='connected-nodes':return im
        d=ImageDraw.Draw(im);p=ease((t-scene['start'])/.6);cx1,cx2=W*.25,W*.72;cy=H*.40
        d.line([(cx1,cy),(cx1+(cx2-cx1)*p,cy)],fill=(251,73,8),width=4)
        for x in[cx1,cx2]:d.ellipse((x-55,cy-55,x+55,cy+55),fill=(3,3,3),outline=(251,73,8),width=3)
        for x,label in[(.25,scene['left_label']),(.72,scene['right_label'])]:
            self.draw_text(im,label,[W*(x-.16),H*.46,W*.32,H*.065],'sans',48,[11,12,12],700,1,records,'label')
        return im
