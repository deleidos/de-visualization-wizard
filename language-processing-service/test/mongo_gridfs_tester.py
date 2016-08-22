import logging
import tempfile
import os.path
import os
from gensim.models import Word2Vec
from pymongo import MongoClient
import gridfs

exists = dbExists = False
model = None
modelName = 'CivilUnrest_mdl'
modelStore = r'newscorpusreader\\NewsCorpus\\ModelStore\\CivilUnrest.mdl'
tmpfilename = ''
most_similar_words = []
terms = ['police', 'shootings']

print ( os.path.getsize( modelStore ))

model = Word2Vec.load(modelStore )
fp = tempfile.NamedTemporaryFile(delete=False, mode='w+b')
# pickle.dump(model, fp)
print ("fp -->", fp.name)
print ( os.path.getsize( fp.name ))
model.save(fp.name)

print ( os.path.getsize( fp.name ))

db = MongoClient()[ modelName ]
fs = gridfs.GridFS( db )
x = fs.put ( fp  filename=modelName )
fs.exists()

## loading from Mongo
# get the Model
# write to a named temporary file and load as above
#

client = MongoClient('localhost',27017)
dbnames = client.database_names()
if modelName in dbnames:
	dbExists = True


db = MongoClient()[ modelName ]
fs = gridfs.GridFS(db)
print ("List --> ", fs.list() )

exists =  fs.exists()
if ( exists ):
	print ("model :", modelName, " Exists")
else:
	print ("model :", modelName, " Does Not Exists")

print ("Number of files -->" +  str( db.fs.files.count() ) )
if exists:
	objectid = db.fs.files.find({}, {"_id" : 1})[0]
	objectid = list ( db.fs.files.find() )[0]['_id']
	print ("model id :", objectid )
	with fs.get(objectid) as fp_read:
		model_in_memory = fp_read.read()
	print ('model_in_memory size -->' + str(len(model_in_memory)))
	# tmpfile = tempfile.NamedTemporaryFile(delete=False, mode='w+b')
	# tmpfilename = tmpfile.name 
	
	with tempfile.NamedTemporaryFile(delete=False, mode='w+b') as temp:
		temp.write(model_in_memory)
		temp.flush()
		tmpfilename = temp.name
		print ("NamedTemporaryFile -->", tmpfilename)
		print ( os.path.getsize( tmpfilename ))
		model = Word2Vec.load(tmpfilename)
if model:
	most_similar_words = model.most_similar(positive=terms, topn=20)
	print ("most_similar_words -->" + str( most_similar_words))
