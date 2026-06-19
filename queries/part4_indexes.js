// queries/part4_indexes.js
// Run: mongosh "<MONGO_URI>" --file queries/part4_indexes.js

use("spotify");

function printExecutionStats(title, explainResult) {
  print("\n" + title);
  printjson({
    executionTimeMillis: explainResult.executionStats.executionTimeMillis,
    totalKeysExamined: explainResult.executionStats.totalKeysExamined,
    totalDocsExamined: explainResult.executionStats.totalDocsExamined,
    nReturned: explainResult.executionStats.nReturned,
    winningPlan: explainResult.queryPlanner.winningPlan
  });
}

function safeDropIndex(collection, indexName) {
  const existingIndexes = collection.getIndexes().map((idx) => idx.name);

  if (existingIndexes.includes(indexName)) {
    collection.dropIndex(indexName);
    print("Dropped existing index: " + indexName);
  } else {
    print("Index does not exist yet, skipping drop: " + indexName);
  }
}

print("\nTask 1: Query analysis and compound index");

safeDropIndex(db.tracks, "idx_genre_danceability_popularity");

const query1 = {
  track_genre: "pop",
  "audio_features.danceability": { $gte: 0.7 }
};
const sort1 = { popularity: -1 };

const beforeIndex = db.tracks.find(query1).sort(sort1).explain("executionStats");
printExecutionStats("Before index", beforeIndex);

db.tracks.createIndex(
  { track_genre: 1, "audio_features.danceability": 1, popularity: -1 },
  { name: "idx_genre_danceability_popularity" }
);

const afterIndex = db.tracks.find(query1).sort(sort1).explain("executionStats");
printExecutionStats("After index", afterIndex);

print("\nTask 2: Index for background work search");

safeDropIndex(db.tracks, "idx_work_music_search");

db.tracks.createIndex(
  {
    explicit: 1,
    "audio_features.instrumentalness": 1,
    "audio_features.speechiness": 1
  },
  { name: "idx_work_music_search" }
);

const workQuery = {
  explicit: false,
  "audio_features.instrumentalness": { $gt: 0.5 },
  "audio_features.speechiness": { $lt: 0.1 }
};

const workExplain = db.tracks.find(workQuery).explain("executionStats");
printExecutionStats("Work music query with index", workExplain);

print("\nTask 3: Covered query check");

const notCovered = db.tracks.find(
  {
    track_genre: "pop",
    popularity: { $gte: 70 }
  }
).explain("executionStats");

printExecutionStats("Original query without projection: not covered", notCovered);

const coveredCandidate = db.tracks.find(
  {
    track_genre: "pop",
    popularity: { $gte: 70 }
  },
  {
    _id: 0,
    track_genre: 1,
    popularity: 1,
    "audio_features.danceability": 1
  }
).explain("executionStats");

printExecutionStats("Covered query candidate with projection", coveredCandidate);

print("\nREADME note:");
print("The original query is not covered because it returns full documents by default.");
print("A covered query requires all filter and projected fields to be included in the index, and _id must be excluded unless it is indexed.");
