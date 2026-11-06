from PIL import Image
import numpy as np
from pathlib import Path
R=Path(__file__).resolve().parents[1]
for key,path in [('hbase','assets/hunapu-sword-2.png'),('hadv','assets/v2/hunapu-sword-fixed-3.png'),('ebase','assets/eileen-sword-3.png'),('eadv','assets/eileen-sword-advanced-2.png')]:
 a=np.array(Image.open(R/path).convert('RGBA'));skin=(a[:,:,0]>140)&(a[:,:,0]>a[:,:,1]*1.08)&(a[:,:,1]>a[:,:,2]*1.10)&(a[:,:,3]>160);yy,xx=np.where(skin);print(key,'ALL',[(int(y),int(np.where(skin[y])[0].min()),int(np.where(skin[y])[0].max()))for y in range(a.shape[0])if skin[y].sum()>3][:22])
