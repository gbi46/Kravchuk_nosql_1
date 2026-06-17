// part4_indexes.js
// Run: mongosh "YOUR_MONGO_URI/spotify" --file queries/part4_indexes.js

use("spotify");

function showExecutionStats(label, cursor) {
  print("
" + label);
  const stats = cursor.explain("executionStats");
  printjson({
    executionTimeMillis: stats.executionStats.executionTimeMillis,
    totalKeysExamined: stats.executionStats.totalKeysExamined,
    totalDocsExamined: stats.executionStats.totalDocsExamined,
    nReturned: stats.executionStats.nReturned,
    winningPlan: stats.queryPlanner.winningPlan
  });
}

print("
Task 1: Query before and after index");
try { db.tracks.dropIndex("idx_genre_danceability_popularity"); } catch (e) { print("Index did not exist before test"); }
const query1 = { track_genre: "pop", "audio_features.danceability": { $gte: 0.7 } };
const projection1 = { _id: 0, track_name: 1, artists: 1, popularity: 1, track_genre: 1, "audio_features.danceability": 1 };
showExecutionStats("Before idx_genre_danceability_popularity", db.tracks.find(query1, projection1).sort({ popularity: -1 }));
db.tracks.createIndex({ track_genre: 1, "audio_features.danceability": 1, popularity: -1 }, { name: "idx_genre_danceability_popularity" });
showExecutionStats("After idx_genre_danceability_popularity", db.tracks.find(query1, projection1).sort({ popularity: -1 }));

print("
Task 2: Work music index");
db.tracks.createIndex({ explicit: 1, "audio_features.instrumentalness": 1, "audio_features.speechiness": 1 }, { name: "idx_work_music_filters" });
const workQuery = { explicit: false, "audio_features.instrumentalness": { $gt: 0.5 }, "audio_features.speechiness": { $lt: 0.1 } };
showExecutionStats("Work music query with idx_work_music_filters", db.tracks.find(workQuery, { _id: 0, track_name: 1, artists: 1, explicit: 1, "audio_features.instrumentalness": 1, "audio_features.speechiness": 1 }));

print("
Task 3: Covered query check");
showExecutionStats("Covered candidate with explicit projection", db.tracks.find({ track_genre: "pop", popularity: { $gte: 70 } }, { _id: 0, track_genre: 1, popularity: 1 }).hint("idx_genre_danceability_popularity"));
print("Original query without projection is not covered because MongoDB must return full documents, while the index contains only track_genre, audio_features.danceability, and popularity.");
