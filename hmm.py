import features
from numpy import zeros,array,histogram,linspace, float32, float64, log2, floor, diff

class EmmissionDistributions(object):
  """

  Emmission distributions

  1. Project a whisker segment to a feature vector

  2. Estimate P(segment|class) using known whiskers and trajectories

  3. Define a function to evaluate P(segment|class).

  Two classes are involved in this model:

    Junk
      Whisker segments not involved in a trajectory

    Whiskers
      Whisker segments involved in some trajectory

  """
  def __init__(self, states, classifier, wvd=None, traj=None, data = None):
    """
    Parameters:
    
    `states`: A list of state names.
              e.g. ["junk","whiskers"]

    `classifier`: A function mapping wvd,traj,fid,wid to an index in states.
                  e.g: lambda wvd,traj,fid,wid: (fid,wid) in invtraj(traj)

    `wvd`: [optional] If specified, `traj` must also be specified.
           A whiskers dictionary.  Will be used to call
           `EmmissionDistributions.estimate.`

    `traj`: [optional] If specified, `wvd` must also be specified. 
            A trajectories dictionary.  Will be used to call
            `EmmissionDistributions.estimate.` 

    `data`: [optional] A table supplied as a 2d ndarray to use as a set
            of feature vectors.  This must conform to the format expected
            internally.  
            
    """
    object.__init__(self)
    self._features = (( "Length(px)"               , features.integrate_path_length ), # Each function maps
                      ( "Median score"             , features.median_score          ), #   whisker segment --> real
                      ( "Angle at folicle (deg)"   , features.root_angle_deg        ),
                      ( "Mean curvature (1/px)"    , features.mean_curvature        ),
                      ( "Follicle x position (px)" , features.follicle_x            ),
                      ( "Follicle y position (px)" , features.follicle_y            ))
    #bins for feature histograms
    self._feature_bin_deltas = zeros( len(self._features) )
    self._feature_bin_mins   = zeros( len(self._features) )

    self._states = states
    self._distributions  =  dict([(s,[]) for s in states]) # stored as log2( probability density )
    self._classifier = classifier
    if not (wvd is None or traj is None):
      self.estimate(wvd,traj,data)

  def feature(self, seg ):
    return array([ f(seg) for name,f in self._features ])  
  
  @staticmethod
  def _count_whiskers(wvd):
    nrows = 0
    for fid,v in wvd.iteritems():
      nrows += len(v)
    return nrows

  def _all_features(self, wvd, traj):
    data = zeros( ( self._count_whiskers(wvd), len(self._features)+3 ) ) #the extra 3 cols are for class id, fid, wid
    def iter():
      for fid,v in wvd.iteritems():
        for wid,w in v.iteritems():
          yield fid,wid,self.feature(w)
    for i,(fid,wid,fv) in enumerate(iter()):
      data[i,0] = self._classifier(wvd,traj,fid,wid)
      data[i,1] = fid
      data[i,2] = wid
      data[i,3:] = fv
    return data

  def estimate(self, wvd, traj, data = None):
    if data is None:
      data = self._all_features(wvd,traj)
    else:
      # need to update classification even if data supplied
      for row in data:
        row[0] = self._classifier(wvd,traj,row[1],row[2])

    nfeat = len(self._features)

    for i in xrange(nfeat):
      ic = 3+i
      v = data[:,ic]     # Determine bins to compute histograms over for each feature
      #avg = v.mean()     # Bounds are limited to 3 times the standard deviation 
      #wid = 3.0*v.std()  #  or the max/min; whichever gives the smaller interval.
      mn  = v.min()      #
      mx  = v.max()      #
      b = linspace( mn, mx , 64 )
      self._feature_bin_deltas[i] = b[1] - b[0]
      self._feature_bin_mins[i]   = b[0]

      for i,state in enumerate(self._states):
        mask = data[:,0]==i
        counts,bb = histogram( v[mask], bins   = b )
        counts = counts.astype(float64) + 1.0 #add one to each bin...gets rid of zeros
        counts /= counts.sum()                #  FIXME: (line above) better way? what's the upper bound on the prob of a bin w 0
        self._distributions[state].append( log2(counts) ) # all counts>0
    
  def _discritize(self, fv): 
    #FIXME: there's a problem here with out of bounds values
    return array( [ floor((val-bmin)/db) for val,db,bmin in zip(fv, \
                                                                self._feature_bin_deltas, \
                                                                self._feature_bin_mins) ] )

  def evaluate(self, seg, state ):
    data = self.feature(seg)
    idx = self._discritize( data )
    logp = [ self._distributions[state][i][j] for i,j in enumerate(idx)]
    return sum(logp)

class EDTwoState(EmmissionDistributions):
  def __init__(self, wvd, traj, data = None, do_estimate = True):
    classifier = self._make_classifer(traj)
    if do_estimate:
      EmmissionDistributions.__init__(self, ["junk","whiskers"], classifier, wvd, traj, data )
    else:
      EmmissionDistributions.__init__(self, ["junk","whiskers"], classifier)

  @staticmethod
  def _itertraj(traj):
    for tid,v in traj.iteritems():
      for fid,wid in v.iteritems():
        yield fid,wid

  @staticmethod
  def _make_classifer(traj):
    frames = set()
    for v in traj.values():
      frames.update( v.keys() )
    labelled = set( list( EDTwoState._itertraj(traj) ) )
    def classifier(wvd,traj,wid,fid):
      return int( (wid,fid) in labelled ) if fid in frames else -1
    return classifier

  def estimate(self, wvd, traj, data = None):
    self._classifier = self._make_classifer(traj)
    EmmissionDistributions.estimate( self, wvd, traj, data )

def iterstates(n):
  yield "start"
  for i in xrange(n):
    yield "junk%d"%i
    yield "whisker%d"%i
  yield "end"

def wcmp(a,b):
  """ A strict ordering whisker segments in a frame """
  return cmp( a.y[0], b.y[0] )

class EDMultiState(EmmissionDistributions):
  def __init__(self, wvd, traj, data = None, do_estimate = True):
    classifier = self._make_classifer( wvd, traj )
    if do_estimate:
      EmmissionDistributions.__init__( self,  self._states, classifier, wvd, traj, data )
    else:
      EmmissionDistributions.__init__( self,  self._states, classifier)

  @staticmethod
  def _itertraj(traj):
    for tid,v in traj.iteritems():
      for fid,wid in v.iteritems():
        yield fid,wid

  def _make_classifer(self, wvd,traj):
    """ 
    Generates the classifier function used in training.
    Also generates the states.
    """
    labelled = set( list( self._itertraj(traj) ) )
    frames = set()
    for v in traj.values():
      frames.update( v.keys() )

    self._nsteps = 0

    names = "junk%d","whisker%d"
    wrowcmp = lambda a,b: wcmp(a[1],b[1])
    classmap = {}
    states   = set()
    for fid,wv in wvd.iteritems():
      t = 0
      for wid,w in sorted( wv.items(), cmp = wrowcmp ):
        if (fid,wid) in labelled: #whisker
          name = names[1]%t
          t+=1
        else: #junk
          name = names[0]%t
        classmap[ (fid,wid) ] = name
        states.add(name)
      self._nsteps = max(self._nsteps,t)
    self._states = list(states)
    statemap = dict( [(n,i) for i,n in enumerate(self._states) ] )
    def classifier(wvd,traj,fid,wid):
      return statemap[ classmap[(fid,wid)] ] if fid in frames else -1
    return classifier

  def estimate(self, wvd, traj, data = None):
    self._classifier = self._make_classifer(wvd,traj)
    EmmissionDistributions.estimate( self, wvd, traj, data )
  
    
class LeftRightModel(object):
  def __init__(self):
    object.__init__(self)
    self.states = None
    self._statemodel = None
    self._startprob   = {} # map dest   -> log2 prob
    self._transitions = {} # map source -> ( map destination -> log2 prob )

  def transition_matrix(self):
    n = len(self.states)
    T = zeros( (n,n) )
    for isrc,src in enumerate(self.states):
      for idst,dst in enumerate(self.states):
        try:
          T[isrc,idst] = self._transitions[ src ][ dst ]
        except KeyError:
          pass
    return T

  def start_matrix(self):
    pass

  def emmissions_matrix(self, whiskers):
    pass

  def viterbi(self, sequence):
    S = self.start_matrix()
    E = self.emmissions_matrix(sequence)
    T = self.transition_matrix()
    pass

  @staticmethod
  def _itertrajinv(traj):
    for tid,v in traj.iteritems():
      for fid,wid in v.iteritems():
        yield (fid,wid),tid

  def train_emmissions(self,wvd,traj,data=None):
    self._statemodel.estimate(wvd,traj,data)

  def train_time_independent(self, wvd,traj):
    S = zeros( 2, dtype = float64 )    #start probabilities
    T = zeros( (2,2),  dtype=float64 ) #transitions: two states - whisker, junk (0 and 1 resp)
    E = zeros( 2, dtype = float64 )    #end probabilities

    simplestates = EDTwoState( wvd, traj, do_estimate = False ) #builds the state space and classifier
    classify = simplestates._classifier
    for fid,wv in wvd.iteritems():
      wids = wvd.keys()
      prev = classify(wvd,traj,fid,wids[0])
      if prev == -1: #frame absent
        continue
      S[prev]++;
      for wid in wids[1:]:
        next = classify(wvd,traj,fid,wid)
        T[prev,next] ++;
        prev = next;
      E[prev]++;

    #normalize to make stochastic matrix/vector
    S /= S.sum()
    E /= E.sum()
    for row in T:
      row /= row.sum()
    S,E,T = map( log2, (S,E,T) )

    self._simple_model = S,T,E,simplestates # just saved for debug/inspection

    #
    # map to the left-right model
    #
    lrstates = EDMultiState( wvd, traj, do_estimate = False )
    self._statemodel = lrstates
    self.states = lrstates._states
    classify = lrstates._classifier

    names = {0:"whisker%d",1:"junk%d"}
    def map_state(state,time):
      n = names[state]
      if state in (1,2):
        n = n%time
      return n
    # start
    for dst,logp in enumerate(S):     
      self._startprob[map_state(dst,0)] = logp
    #middle to end
    for src,row in enumerate(T): # no start as source state or end state
      for dst,logp in enumerate(row):
        for time in xrange( lrmodel._nsteps ):
          self._transitions.setdefault( map_state(src,time), {} )[map_state(dst,time)] = logp


  def train_time_dependent(wvd,traj):
    pass

