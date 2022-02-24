class Search:
    types = ["artist", "song", "podcast", "album", "tvshow", "movie"]
    comparators = ["=", "<", ">"]
    two_comparators = ["!=", "<>", ">=", "<="]

    def __init__(self, search_string):
        self.status = ""
        self.type = ""
        self.genre = ""
        self.movie_year = ""
        self.song_length = ""
        self.artist_metadata_count = ""
        self.title = ""

        search_string += " "
        for item in search_string.split(" "):
            if item == "":
                continue
            if ":" not in item:
                self.status = "Wrong Format, must be type:value, if value contains space, use quotation marks"
                return
            else:
                item_split = item.split(":")

                if item_split[0].lower() in Search.types:
                    if self.type != "":
                        self.status = ""
                        return
                    self.type = item_split[0].lower()
                    self.title = item_split[1].replace("'", " ").replace('"', " ")

                elif item_split[0].lower() == "genre":
                    if self.genre != "":
                        self.status = "Repeated Genre"
                        return
                    self.genre = item_split[1].replace("'", " ").replace('"', " ")

                elif item_split[0].lower() == "year":
                    if self.movie_year != "":
                        self.status = "Repeated Year"
                        return
                    self.movie_year = item_split[1]
                    # Check if self.movie_year contains symbols in comparators/two_comparators
                    if self.movie_year.isnumeric():
                        self.movie_year = "=" + self.movie_year # no comparator
                    elif self.movie_year[:1] in Search.comparators and self.movie_year[1:].isnumeric():
                        pass # one comparator
                    elif self.movie_year[:2] in Search.two_comparators and self.movie_year[2:].isnumeric():
                        pass # two comparators
                    else:
                        self.status = "Wrong syntax on movie year"
                        return

                elif item_split[0].lower() == "length":
                    if self.song_length != "":
                        self.status = "Repeated Length"
                        return
                    self.song_length = item_split[1]
                    # Check if self.song_length contains symbols in comparators/two_comparators
                    if self.song_length.isnumeric():
                        self.song_length = "=" + self.song_length # no comparator
                    elif self.song_length[:1] in Search.comparators and self.song_length[1:].isnumeric():
                        pass # one comparator
                    elif self.song_length[:2] in Search.two_comparators and self.song_length[2:].isnumeric():
                        pass # two comparators
                    else:
                        self.status = "Wrong syntax on song length"
                        return

                elif item_split[0].lower() == "metadatacount":
                    if self.artist_metadata_count != "":
                        self.status = "Repeated Metadata Count"
                        return
                    self.artist_metadata_count = item_split[1]
                    # Check if self.artist_metadata_count contains symbols in comparators/two_comparators
                    if self.artist_metadata_count.isnumeric():
                        self.artist_metadata_count = "=" + self.artist_metadata_count # no comparator
                    elif self.artist_metadata_count[:1] in Search.comparators and self.artist_metadata_count[1:].isnumeric():
                        pass # one comparator
                    elif self.artist_metadata_count[:2] in Search.two_comparators and self.artist_metadata_count[2:].isnumeric():
                        pass # two comparators
                    else:
                        self.status = "Wrong syntax on artist metadata count"
                        return

        # check logical errors
        if self.type == "" or self.title == "":
            self.status = "No type or no search content!"
            return
        if self.type != "movie" and self.movie_year != "":
            self.status = "Year is only for movies"
            return
        if self.type != "song" and self.song_length != "":
            self.status = "Length is only for songs"
            return
        if self.type != "artist" and self.artist_metadata_count != "":
            self.status = "Metadata count is only for artists"
            return
        if self.genre != "" and self.type == "artist":
            self.status = "Genre is not for artists"
            return

    def construct_search(self):
        if self.type == "artist":
            return self.artist_without_genre()
        elif self.type == "song":
            if self.genre == "":
                return self.song_without_genre()
            else:
                return self.song_with_genre()
        elif self.type == "podcast":
            if self.genre == "":
                return self.podcast_without_genre()
            else:
                return self.podcast_with_genre()
        elif self.type == "album":
            if self.genre == "":
                return self.album_without_genre()
            else:
                return self.album_with_genre()
        elif self.type == "tvshow":
            if self.genre == "":
                return self.tvshow_without_genre()
            else:
                return self.tvshow_with_genre()
        elif self.type == "movie":
            if self.genre == "":
                return self.movie_without_genre()
            else:
                return self.movie_with_genre()

    def artist_without_genre(self):
        search_string = """
                    select
                        a.*, count(amd.md_id) as count
                    from
                        mediaserver.artist a left outer join mediaserver.artistmetadata amd on (a.artist_id=amd.artist_id)
                    where
                        lower(artist_name) ~ lower(%s)
                    group by a.artist_id, a.artist_name
                    """
        search_variables = [self.title]
        if self.artist_metadata_count != "":
            # Check if artist_metadata_count contains two_comparators

            if any(i in self.artist_metadata_count for i in Search.two_comparators):
                search_string += """
                having count(amd.md_id)""" + self.artist_metadata_count[0] +  self.artist_metadata_count[1]+ "%s"
                search_variables.append(self.artist_metadata_count[2:])
            else:
                search_string += """
                            having count(amd.md_id)""" + self.artist_metadata_count[0] + "%s"
                search_variables.append(self.artist_metadata_count[1:])

        search_string += """
                    order by a.artist_name"""
        return search_string, tuple(search_variables)

    def song_without_genre(self):
        search_string = """
                    select 
                        s.song_id, s.song_title, string_agg(saa.artist_name,',') as artists
                    from 
                        mediaserver.song s left outer join 
                        (mediaserver.Song_Artists sa join mediaserver.Artist a on (sa.performing_artist_id=a.artist_id)
                        ) as saa  on (s.song_id=saa.song_id)
                    where
                        lower(song_title) ~ lower(%s)
                    """
        search_variables = [self.title]
        if self.song_length != "":
            # Check if song_length contains two_comparators

            if any(i in self.song_length for i in Search.two_comparators):
                search_string += "and s.length " + self.song_length[0] + self.song_length[1] + "%s"
                search_variables.append(self.song_length[2:])
            else:
                search_string += "and s.length " + self.song_length[0] + "%s"
                search_variables.append(self.song_length[1:])

        search_string += """
                    group by s.song_id, s.song_title
                    order by s.song_id
                    """
        return search_string, tuple(search_variables)

    def song_with_genre(self):
        search_string = """
                            select 
                                s.song_id, s.song_title, string_agg(saa.artist_name,',') as artists
                            from 
                                mediaserver.song s left outer join 
                                (mediaserver.Song_Artists sa join mediaserver.Artist a on (sa.performing_artist_id=a.artist_id)
                                ) as saa on (s.song_id=saa.song_id) left outer join
                                mediaserver.Album_Songs als on (s.song_id = als.song_id) left outer join
                                mediaserver.AlbumMetaData amd on (als.album_id = amd.album_id) join
                                mediaserver.MetaData md on (amd.md_id = md.md_id)
                            where
                                lower(song_title) ~ lower(%s) and
                                lower(md.value) ~ lower(%s)
                            """
        search_variables = [self.title]
        if self.song_length != "":
            # Check if song_length contains two_comparators

            if any(i in self.song_length for i in Search.two_comparators):
                search_string += "and s.length " + self.song_length[0] + self.song_length[1] + "%s"
                search_variables.append(self.song_length[2:])
            else:
                search_string += "and s.length " + self.song_length[0] + "%s"
                search_variables.append(self.song_length[1:])

        search_string += """
                    group by s.song_id, s.song_title
                    order by s.song_id
                    """
        return search_string, tuple(search_variables)

    def podcast_without_genre(self):
        search_string = """
        select 
                p.*, pnew.count as count  
            from 
                mediaserver.podcast p, 
                (select 
                    p1.podcast_id, count(*) as count 
                from 
                    mediaserver.podcast p1 left outer join mediaserver.podcastepisode pe1 on (p1.podcast_id=pe1.podcast_id) 
                    group by p1.podcast_id) pnew 
            where p.podcast_id = pnew.podcast_id
            and p.podcast_title ~ lower(%s)
        """
        search_variables = [self.title]
        return search_string, tuple(search_variables)

    def podcast_with_genre(self):
        search_string = """
        select 
                p.*, pnew.count as count  
            from 
                mediaserver.podcast p left outer join 
                mediaserver.podcastmetadata pmd on (p.podcast_id = pmd.podcast_id) left outer join 
                mediaserver.metadata md on (pmd.metadata_id = md.metadata_id), 
                (select 
                    p1.podcast_id, count(*) as count 
                from 
                    mediaserver.podcast p1 left outer join mediaserver.podcastepisode pe1 on (p1.podcast_id=pe1.podcast_id) 
                    group by p1.podcast_id) pnew 
            where p.podcast_id = pnew.podcast_id
            and p.podcast_title ~ lower(%s)
            and md.md_value ~ lower(%s)
        """
        search_variables = [self.title, self.genre]
        return search_string, tuple(search_variables)

    def album_without_genre(self):
        search_string = """
        select 
                a.album_id, a.album_title, anew.count as count, anew.artists
            from 
                mediaserver.album a, 
                (select 
                    a1.album_id, count(distinct as1.song_id) as count, array_to_string(array_agg(distinct ar1.artist_name),',') as artists
                from 
                    mediaserver.album a1 
            left outer join mediaserver.album_songs as1 on (a1.album_id=as1.album_id) 
            left outer join mediaserver.song s1 on (as1.song_id=s1.song_id)
            left outer join mediaserver.Song_Artists sa1 on (s1.song_id=sa1.song_id)
            left outer join mediaserver.artist ar1 on (sa1.performing_artist_id=ar1.artist_id)
                group by a1.album_id) anew
            where a.album_id = anew.album_id
            and lower(a.album_title) ~ lower(%s)"""
        search_variables = [self.title]
        return search_string, tuple(search_variables)

    def album_with_genre(self):
        search_string = """
        SELECT distinct a.album_id,a.album_title,
            COUNT(distinct song_id) as "song_count",
            array_to_string(array_agg(distinct ar1.artist_name),',') as artists
        FROM mediaserver.album a
        LEFT OUTER JOIN mediaserver.album_songs as1 USING (album_id)
        LEFT OUTER JOIN mediaserver.Song_Artists sa1 USING (song_id)
        LEFT OUTER JOIN mediaserver.artist ar1 on (sa1.performing_artist_id=ar1.artist_id)
        JOIN (mediaserver.MediaItem
            NATURAL JOIN mediaserver.MediaItemMetaData
            NATURAL JOIN mediaserver.metadata
            NATURAL JOIN mediaserver.metadatatype) songmd ON (as1.song_id=songmd.media_id)
        WHERE lower(a.album_title) ~ lower(%s)
        AND lower(song.md_value) ~ lower(%s)
        GROUP BY a.album_id;
        """
        search_variables = [self.title, self.genre]
        return search_string, tuple(search_variables)

    def tvshow_without_genre(self):
        search_string = """
            select 
                t.*, tnew.count as count  
            from 
                mediaserver.tvshow t, 
                (select 
                    t1.tvshow_id, count(te1.media_id) as count 
                from 
                    mediaserver.tvshow t1 left outer join mediaserver.TVEpisode te1 on (t1.tvshow_id=te1.tvshow_id) 
                    group by t1.tvshow_id) tnew 
            where t.tvshow_id = tnew.tvshow_id and lower(tvshow_title) ~ lower(%s)
            order by t.tvshow_id;"""
        search_variables = [self.title]
        return search_string, tuple(search_variables)

    def tvshow_with_genre(self):
        # TODO: Complete this!
        search_string = """
        SELECT tv.*
        FROM  mediaserver.TVShow tv
            LEFT OUTER JOIN mediaserver.TVEpisode tve USING (tvshow_id)
            FULL OUTER JOIN
        (mediaserver.VideoMedia
        NATURAL JOIN mediaserver.MediaItemMetaData
        NATURAL JOIN mediaserver.metadata
        NATURAL JOIN mediaserver.metadatatype) videomd USING (media_id)
        FULL OUTER JOIN mediaserver.Movie m ON (videomd.media_id=m.movie_id)
        WHERE lower(tv.tvshow_title) ~ lower (%s)
        AND videomd.md_value ~ lower(%s)
        """
        search_variables = [self.title, self.genre]
        return search_string, tuple(search_variables)

    def movie_without_genre(self):
        search_string = """
                select
                    m.*
                from
                    mediaserver.movie m
                where lower(movie_title) ~ lower (%s)
                        """
        search_variables = [self.title]
        if self.movie_year != "":

            # Check if movie_year contains two_comparators
            if any(i in self.movie_year for i in Search.two_comparators):
                search_string += "and m.release_year " + self.movie_year[0]+ self.movie_year[1] + "%s"
                search_variables.append(self.movie_year[2:])
            else:
                search_string += "and m.release_year " + self.movie_year[0] + "%s"
                search_variables.append(self.movie_year[1:])

        search_string += "order by m.movie_id"
        return search_string, tuple(search_variables)

    def movie_with_genre(self):
        search_string = """
        select
            m.*
        FROM  mediaserver.TVShow tv
            LEFT OUTER JOIN mediaserver.TVEpisode tve USING (tvshow_id)
            FULL OUTER JOIN
        (mediaserver.VideoMedia
        NATURAL JOIN mediaserver.MediaItemMetaData
        NATURAL JOIN mediaserver.metadata
        NATURAL JOIN mediaserver.metadatatype) videomd USING (media_id)
        FULL OUTER JOIN mediaserver.Movie m ON (videomd.media_id=m.movie_id)
        WHERE lower(movie_title) ~ lower (%s)
        AND videomd.md_value ~ lower(%s)
        """
        search_variables = [self.title, self.genre]
        if self.movie_year != "":

             # Check if movie_year contains two_comparators
            if any(i in self.movie_year for i in Search.two_comparators):
                search_string += "and m.release_year " + self.movie_year[0] +self.movie_year[1] + "%s"
                search_variables.append(self.movie_year[2:])
            else: 
                search_string += "and m.release_year " + self.movie_year[0] + "%s"
                search_variables.append(self.movie_year[1:])

        search_string += "order by m.movie_id"
        return search_string, tuple(search_variables)
