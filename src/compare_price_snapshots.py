"""Compare the verified original August snapshot with a later Yahoo vintage."""
import argparse,json
from pathlib import Path
import numpy as np,pandas as pd
from src.validate_cutoff import sha256_file

def compare(original,new,original_forecasts,new_forecasts,output):
    if output.exists():raise FileExistsError('Comparison output already exists.')
    root=Path(__file__).resolve().parents[1]
    expected=json.loads((root/'forecasts/2026-09-30-v0.1/manifest.json').read_text())['input_sha256']
    if sha256_file(original)!=expected:raise ValueError('Original input does not match the frozen hash.')
    a=pd.read_csv(original,parse_dates=['Date']).set_index('Date');b=pd.read_csv(new,parse_dates=['Date']).set_index('Date')
    if not a.index.equals(b.index) or set(a.columns)!=set(b.columns):raise ValueError('Different dates or assets.')
    b=b[a.columns];ra=np.log(a/a.shift(1)).iloc[1:];rb=np.log(b/b.shift(1)).iloc[1:]
    rows=[]
    for asset in a.columns:
        delta=b[asset]-a[asset];rd=rb[asset]-ra[asset];ratios=b[asset]/a[asset]
        rows.append({'asset':asset,'different_price_cells':int(delta.ne(0).sum()),'max_absolute_price_difference':float(delta.abs().max()),
            'max_absolute_log_return_difference':float(rd.abs().max()),'min_new_over_original_price_ratio':float(ratios.min()),'max_new_over_original_price_ratio':float(ratios.max())})
    f=pd.read_csv(original_forecasts);g=pd.read_csv(new_forecasts)
    joined=f.merge(g,on=['target_month','method'],suffixes=('_original','_reconstructed'),validate='one_to_one')
    joined['difference']=joined.forecast_decimal_original-joined.forecast_decimal_reconstructed
    output.mkdir(parents=True)
    pd.DataFrame(rows).to_csv(output/'asset_comparison.csv',index=False,float_format='%.17g')
    joined[['target_month','method','forecast_decimal_original','forecast_decimal_reconstructed','difference']].to_csv(output/'forecast_comparison.csv',index=False,float_format='%.17g')
    maxdate=(b.SPY-a.SPY).abs().idxmax()
    summary={'original_sha256':sha256_file(original),'original_frozen_hash_match':True,'new_sha256':sha256_file(new),'rows':len(a),'same_dates':True,'same_assets':True,
        'different_price_cells':int((b-a).ne(0).sum().sum()),'max_absolute_price_difference':float((b-a).abs().max().max()),'max_absolute_log_return_difference':float((rb-ra).abs().max().max()),
        'max_absolute_forecast_difference_decimal':float(joined.difference.abs().max()),'max_absolute_forecast_difference_percentage_points':float(100*joined.difference.abs().max()),
        'spy_price_example':{'date':str(maxdate.date()),'original':float(a.loc[maxdate,'SPY']),'new':float(b.loc[maxdate,'SPY'])},
        'interpretation':'Numeric prices differ, not only formatting. Near-proportional price adjustments largely cancel in log-return ratios; cause of provider changes is not independently established.',
        'source_sha256':sha256_file(Path(__file__))}
    (output/'comparison.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ['original','new','original-forecasts','new-forecasts','output']:p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();compare(a.original,a.new,a.original_forecasts,a.new_forecasts,a.output)
