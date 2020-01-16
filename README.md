# Correlation Server

Running the separate components the same ways as specified in handout
#### Data Generation:
<pre>
python generate_pnl_data.py -o [output directory] -n [num files]
</pre>

#### Server:
<pre>
python correlation_server.py --port [port number] --path_to_pnls [folder of data]
</pre>

<!--HTTP server
Read folders recursively-->

#### Client:
<pre>
python compute_pnl_correlation.py --pnl [folders and files separated by space] --server [host:port]
                                  --start_date [YYYYMMDD] --end_date [YYYYMMDD] --top [num top correlations]
</pre>