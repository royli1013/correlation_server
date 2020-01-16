# Correlation Server

Running the separate components the same ways as specified in handout:
#### Data Generation:
<pre>
python generate_pnl_data.py -o [output directory] -n [num files] -f
</pre>
Generates returns data for 30 instruments for 2500 weekdays starting from 2009 01 01.
Then, generates n alphas based on return, smooths them, and writes pnl and turnover to files.

#### Server:
<pre>
python correlation_server.py --port [port number] --path_to_pnls [folders and files separated by space]
</pre>

Reads each file and all file in given folders recursively, treating each file as a pnl file.
Assumes that all files have the same date indices. Accepts connections one at a time, and calculates
correlation of pnl data from request against all pnl files specified.

#### Client:
<pre>
python compute_pnl_correlation.py --pnl [folders and files separated by space] --server [host:port]
                                  --start_date [YYYYMMDD] --end_date [YYYYMMDD] --top [num top correlations]
</pre>
Reads each file and all files in given folders recursively and sends a correlation request 
to the specified server. Either prints error from server if correlation cannot be calculated or prints
the top results from the request.

#### Unit Tests:
<pre>
python -m unittest discover
</pre>
Run inside the current directory


## Some Notes About Implementation
- I have tried to use as much vectorized operations as possible in generating data. To do this, instead
  of generating an alpha, smoothing it, calculating pnl and tvr, and writing it to a file (which seemed
  like the most natural way), I decided to generate all the alphas in one step, smoothing all of them in
  another step, calculate all the pnl and tvr, then write them to files concurrently. I found this to be
  much faster than generating one by one, but at the price of using a lot more memory. While memory is not
  a big concern, I did try to optimize a bit more by using the same arrays if possible and freeing up unused
  data.
- The server is an HTTP server. A even ligher server would have sufficed, such as a simple TCP server, 
  but I felt like the easiness of use and general resources for HTTP servers outweighs having a lighter server.
  Plus, this way, it would be easier for us to add a monitoring/UI feature.
- Since the client sends an aggregation of pnl files to the server, the pnl files can also be seen as a
  pnl pool, so I decided to use the same class for the actual pool in the server and the files the client sends.
  So far, I think this has worked quite well, as I am able to delegate a lot of common functionalities to the
  PnlPool object (such as reading the pnl files).
- The PnlPool object assumes all files it reads have the same indices (dates) and just sets internal indices
  to the dates from the first file it reads. In addition, in this project, I am assuming that all pnl files
  start from the same date and contain only weekdays with no missing dates (ie. all files can be viewed as
  results from generate_pnl_data.py)
- I have decided to send JSON over HTTP to communicate between the server and the client. Since we are not
  expecting to send thousands (or even hundreds) of pnl files over the network, I am not worried about
  the performance for this part. There are definitely better ways than sending strings over the network,
  and it would be worth investigating if we ever decide to send large amounts of files.
- In an effort to make correlation calculation reusable, I have made the correlation requesting function
  a library function that takes in a CorrelationRequest object, along with host and port. This way, to send
  a request, all the client needs to do is build a CorrelationRequest object, which only requires a PnlPool.
- I used very little multithreading in this project, the only place being writing generated pnl data to files.
  After some research and testing, I found that the vectorized numpy operations uses all CPUs by default.
  So, instead of trying out my own multithreading methods, I decided to try to use vectorized operations
  wherever I can to avoid having to use multithreading and dealing with the GIL or multiprocessing and copying
  larges amounts of memory.
- The server is only able to process one request at a time. After much debate, I decided to go with this simple
  solution. My initial idea was to have a master thread accept requests and push them into a concurrent queue
  while many worker threads constantly pull from the queue and do the actual calculations. This has a number of
  drawbacks, however. Due to GIL, we can't have a truly multithreaded solution. So, instead of threads, we can
  use processes. But, since processes do not share the same memory, we would need to copy our pnl pool to all
  of the worker processes. Since our pool can be very big, I felt like this was not feasible. In the end,
  instead of dealing with threads, memory, and possibly over subscription, I decided to have the server focus
  all of its computation power on one request at a time, which can be just as effective when the number of
  simultaneous requests is low.
- I have only tested data generation and the server with 25,000 pnl files. On my 4 CPU machine, generating 
  the 25,000 files took about 20 mins, with the longest step being smoothing the alphas, which took close
  to 8 mins. Starting the server with 25000 files took about 5 mins, and calculating correlation with only
  one file in the request took 0.7 sec.


## Possible Improvements
- Logging and exception handling can definitely be improved. Currently, I am just printing mostly performance
  related data to the console. Since the server is meant to be long lived, ideally, it would be nice to have
  different levels of logging with more information written to a permanent file.
- I am assuming that all pnl files have the same dates and did not implement a lot of checks for this, so having
  a pnl pool with files that don't have the same length will lead to undefined behaviour. As a very simple
  sanity check, we could, each time we read a file, verify that its date column matches all the other date
  columns from other files.
- It would also be relatively simple to deal with missing dates. We could just say that the pnl and turnover
  for that day is 0.
- It might be better for CorrelationRequest and CorrelationResponse classes to define their own ways of
  converting to and loading from JSON. This way, if the implementation for those classes change, we would have
  a more consistent place for updating the JSON conversion logic.
- We could potentially get a performance upgrade by splitting the pnl pool into smaller chunks and using
  different processes to find the top correlations for each chunk before finding the top overall correlations.
  However, due to the nature of numpy and the fact that the vectorized operations already take up majority of
  computation power, I feel like even if there is a performance boost, it would not be significant. This would
  involve changing a fairly large chunk of code, especially for PnlPool
- Smoothing currently takes the most time (when I tested on 25,000 files). I had some trouble finding resources
  on exponential smoothing where the two parameters don't add to 1, so I am doing that step somewhat iteratively.
  All operations in the loops are vectorized, however, and we are looping through the number of days, which is
  fixed at 2500. So, I don't know if there are ways of doing that part a lot faster.

## Known Bugs (so far)
I am not expecting this project to have no bugs in the current state. With the unit tests for all the major
components, I am fairly confident that calculations should be correct and that both the server and the client
can handle most data thrown at them. But, for this to be production ready, we would need to do more unit test
and integration test as well as possibly doing type checking for the public methods (we would also probably
not use tornado in a production environment). Will be adding more to this list as more bugs are discovered.
- In Windows, the server cannot be killed just with Ctrl-C. I think this is due to it not sending a
  KeyBoardInterrupt? To kill it, I had to do Ctrl-C then send a request to the server.
- The server and client cannot infer relative file path if we are not running them at the root directory of
  the project. I feel like this should be possible, but I have not spent a lot of time on this part