"""Download a new Yahoo snapshot without overwriting any existing freeze."""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import urllib.request
import pandas as pd
import exchange_calendars as xc
from src.validate_cutoff import EXPECTED_ETFS

START='2015-01-01'
END='2026-10-08' # Exclusive: no observation later than 7 October.

def assemble(folder):
    series={};hashes={};retrieved={}
    for symbol in EXPECTED_ETFS:
        path=folder/(symbol+'.json');payload=json.loads(path.read_text())
        chart=payload['chart']
        if chart.get('error') or not chart.get('result'):raise ValueError(f'Yahoo error for {symbol}')
        result=chart['result'][0]
        if result['meta']['symbol']!=symbol:raise ValueError('Unexpected ticker response')
        dates=pd.to_datetime(result['timestamp'],unit='s',utc=True).tz_convert('America/New_York').tz_localize(None).normalize()
        if dates.has_duplicates or not dates.is_monotonic_increasing:raise ValueError('Invalid response dates')
        series[symbol]=pd.Series(result['indicators']['adjclose'][0]['adjclose'],index=dates)
        hashes[symbol]=hashlib.sha256(path.read_bytes()).hexdigest()
        retrieved[symbol]=datetime.fromtimestamp(path.stat().st_mtime,timezone.utc).isoformat()
    prices=pd.DataFrame(series).sort_index(axis=1);prices.index.name='Date'
    calendar=xc.get_calendar('XNYS',start=START,end='2026-12-07')
    sessions=calendar.sessions
    if sessions.tz is not None:sessions=sessions.tz_localize(None)
    pd.DataFrame({'Date':sessions}).to_csv(folder/'nyse_sessions.csv',index=False)
    original=json.loads((Path(__file__).resolve().parents[1]/'forecasts/2026-09-30-v0.1/manifest.json').read_text())['input_sha256']
    for cutoff,name in [('2026-08-31','august'),('2026-10-07','october')]:
        panel=prices.loc[:cutoff];path=folder/(name+'_adjusted_close.csv');panel.to_csv(path)
        digest=hashlib.sha256(path.read_bytes()).hexdigest()
        source={'price_source':'Yahoo Finance chart API, query1.finance.yahoo.com','price_column':'indicators.adjclose[0].adjclose',
            'retrieved_at_utc':max(retrieved.values()),'ticker_retrieved_at_utc':retrieved,'input_sha256':digest,
            'calendar_source':'exchange_calendars XNYS; 2026 holidays checked against NYSE published schedule',
            'calendar_package_version':xc.__version__,'request_start_inclusive':START,'request_end_exclusive':END,
            'raw_response_sha256':hashes,'original_august_sha256':original,
            'original_august_byte_match':digest==original if name=='august' else None,
            'snapshot_note':'Current download, not recovery of the original file. Historical adjusted prices can incorporate later distributions or provider revisions.'}
        (folder/(name+'_provenance.json')).write_text(json.dumps(source,indent=2)+'\n')
        print(name,len(panel),digest,'original byte match',digest==original)

def download(folder):
    if folder.exists():raise FileExistsError('A snapshot directory already exists; choose a new path.')
    folder.mkdir(parents=True)
    start=int(datetime.fromisoformat(START).replace(tzinfo=timezone.utc).timestamp())
    end=int(datetime.fromisoformat(END).replace(tzinfo=timezone.utc).timestamp())
    for symbol in EXPECTED_ETFS:
        url=f'https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?period1={start}&period2={end}&interval=1d&events=div%2Csplits'
        request=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
        with urllib.request.urlopen(request,timeout=40) as response:body=response.read()
        # Keep the exact response, even if validation later fails; never fill missing values.
        (folder/(symbol+'.json')).write_bytes(body)
    assemble(folder)

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('folder',type=Path)
    p.add_argument('--assemble-existing-responses',action='store_true')
    a=p.parse_args();assemble(a.folder) if a.assemble_existing_responses else download(a.folder)
