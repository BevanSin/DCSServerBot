CREATE TABLE music_playlists(name TEXT NOT NULL, song_id INTEGER NOT NULL, song_file TEXT NOT NULL);
CREATE TABLE music_servers(server_name TEXT NOT NULL, playlist_name TEXT NOT NULL, PRIMARY KEY (server_name));
CREATE SEQUENCE music_song_id_seq;
