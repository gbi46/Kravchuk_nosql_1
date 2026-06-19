// queries/part3_analytics.js
// Run: mongosh "<MONGO_URI>" --file queries/part3_analytics.js

use("spotify");

print("\nTask 1: Top-10 artists by average popularity");
printjson(
  db.tracks.aggregate([
    { $unwind: "$artists" },
    {
      $group: {
        _id: "$artists",
        track_count: { $sum: 1 },
        avg_popularity: { $avg: "$popularity" }
      }
    },
    { $match: { track_count: { $gte: 5 } } },
    {
      $project: {
        _id: 0,
        artist: "$_id",
        track_count: 1,
        avg_popularity: { $round: ["$avg_popularity", 1] }
      }
    },
    { $sort: { avg_popularity: -1, track_count: -1 } },
    { $limit: 10 }
  ]).toArray()
);

print("\nTask 2: Track distribution by mood");
printjson(
  db.tracks.aggregate([
    {
      $project: {
        mood: {
          $switch: {
            branches: [
              {
                case: {
                  $and: [
                    { $gte: ["$audio_features.valence", 0.5] },
                    { $gte: ["$audio_features.energy", 0.5] }
                  ]
                },
                then: "happy"
              },
              {
                case: {
                  $and: [
                    { $lt: ["$audio_features.valence", 0.5] },
                    { $gte: ["$audio_features.energy", 0.5] }
                  ]
                },
                then: "angry"
              },
              {
                case: {
                  $and: [
                    { $gte: ["$audio_features.valence", 0.5] },
                    { $lt: ["$audio_features.energy", 0.5] }
                  ]
                },
                then: "calm"
              }
            ],
            default: "sad"
          }
        }
      }
    },
    { $group: { _id: "$mood", track_count: { $sum: 1 } } },
    { $project: { _id: 0, mood: "$_id", track_count: 1 } },
    { $sort: { track_count: -1 } }
  ]).toArray()
);

print("\nTask 3: Most dance-oriented genres");
printjson(
  db.tracks.aggregate([
    {
      $group: {
        _id: "$track_genre",
        track_count: { $sum: 1 },
        avg_danceability: { $avg: "$audio_features.danceability" },
        avg_energy: { $avg: "$audio_features.energy" },
        avg_valence: { $avg: "$audio_features.valence" }
      }
    },
    { $match: { track_count: { $gte: 100 } } },
    {
      $project: {
        _id: 0,
        genre: "$_id",
        track_count: 1,
        avg_danceability: { $round: ["$avg_danceability", 3] },
        avg_energy: { $round: ["$avg_energy", 3] },
        avg_valence: { $round: ["$avg_valence", 3] }
      }
    },
    { $sort: { avg_danceability: -1, avg_energy: -1, avg_valence: -1 } },
    { $limit: 20 }
  ]).toArray()
);
