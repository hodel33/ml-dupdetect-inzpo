# Standard modules
import os
import psutil
from datetime import datetime

# Django imports
from core.models import Include_Episode, PotentialDuplicate


class Main():
    """
    A class for managing podcast episode data, handling tasks like filtering, updating, similarity analysis, and database operations.
    """

    def print_ram_usage(self, message="") -> None:
        '''Prints the current RAM usage in megabytes, optionally with a custom message for context.'''
        
        process = psutil.Process(os.getpid())
        ram_usage = process.memory_info().rss / (1024**2)  # Convert bytes to MB
        print(f"RAM USAGE ({message}): {ram_usage:.2f} MB")


    def duration_similarity(self, duration1: int, duration2: int) -> float:
        '''Calculates the similarity between two episode durations as a float between 0 and 1.'''
            
        max_duration = max(duration1, duration2)
        if max_duration == 0:
            return 1.0
        
        return 1.0 - abs(duration1 - duration2) / max_duration
    

    def vectorize_episode_data(self, episodes) -> tuple:
        '''Converts the names and descriptions of a list of episodes into TF-IDF weighted numerical vectors.'''

        from sklearn.feature_extraction.text import TfidfVectorizer

        # Separate names and descriptions
        names = [ep.ep_name for ep in episodes]
        descriptions = [ep.ep_description for ep in episodes]

        # Convert the names and descriptions into numerical vectors using TF-IDF (Term Frequency-Inverse Document Frequency)
        # Using TF-IDF for text similarity as it balances term frequency across documents.
        name_vectorizer = TfidfVectorizer()
        name_tfidf_matrix = name_vectorizer.fit_transform(names)

        description_vectorizer = TfidfVectorizer()
        description_tfidf_matrix = description_vectorizer.fit_transform(descriptions)

        return name_tfidf_matrix, description_tfidf_matrix
    

    def compute_similarities(self, name_tfidf_matrix, description_tfidf_matrix) -> tuple:
        '''Computes the pairwise cosine similarities for episode names and descriptions using their TF-IDF matrices.'''

        from sklearn.metrics.pairwise import cosine_similarity

        # Compute pairwise cosine similarities for names and descriptions
        # Using Cosine similarities to measure the angle between TF-IDF vectors, ideal for text similarity.
        name_similarities = cosine_similarity(name_tfidf_matrix)
        description_similarities = cosine_similarity(description_tfidf_matrix)

        return name_similarities, description_similarities
    
    
    def identify_all_potential_duplicates(self, all_episodes, name_similarities, description_similarities, 
                                          name_thresh, desc_thresh, dur_thresh, new_episodes=None, new_ep_id_to_index=None) -> list:
        '''Identifies groups of episodes that are potential duplicates based on similarity thresholds for names, descriptions and durations.'''
              
        pot_duplicate_groups = []  # Keep track of episodes (in groups) marked as potential duplicates

        # Separate thresholds for episode name, episode description, and episode duration (1 = 100% similarity)
        # These thresholds were empirically determined to balance the trade-off between false positives and true positives
        name_threshold = name_thresh
        description_threshold = desc_thresh
        duration_threshold = dur_thresh

        # If new_episodes is None -> compare all episodes to themselves; if new_episodes is provided -> compare only new episodes against all
        loop_episodes = new_episodes if new_episodes is not None else all_episodes

        for i, episode in enumerate(loop_episodes):

            current_group = [episode] # Initialize a new potential duplicate group with the current episode

            # Skip if episode is already in any of the duplicate groups
            if any(episode in group for group in pot_duplicate_groups):
                continue

            for j in range(i + 1, len(all_episodes)):
                
                # Skip if episode being compared is already in any of the duplicate groups
                if any(all_episodes[j] in group for group in pot_duplicate_groups):
                    continue

                # Skip episode self comparison
                if episode.ep_id == all_episodes[j].ep_id: 
                    continue

                # Use the mapping for efficient index lookups
                # 'j' is always from 'all_episodes', so no need to change
                episode_i_index = new_ep_id_to_index[episode.ep_id] if new_ep_id_to_index is not None else i

                # Calculate the similarities between the current episode and the episode being compared
                name_similarity = name_similarities[episode_i_index][j]
                desc_similarity = description_similarities[episode_i_index][j]
                dur_similarity = self.duration_similarity(episode.ep_duration_sec, all_episodes[j].ep_duration_sec)

                # Check if the episodes meet all the similarity thresholds
                if name_similarity > name_threshold and desc_similarity > description_threshold and dur_similarity > duration_threshold:
                    current_group.append(all_episodes[j])

            # Add the current group to the list of potential duplicate groups if it has more than one episode
            if len(current_group) > 1:
                pot_duplicate_groups.append(current_group)

        return pot_duplicate_groups
    
    
    def filter_new_potential_duplicates(self, pot_duplicate_groups, existing_combos, all_ep_id_to_index, 
                                        name_similarities, description_similarities, new_ep_id_to_index=None) -> list:
        '''Filters out already identified potential duplicates and prepares new ones for database insertion.'''
        
        new_potential_duplicates = []

        for group in pot_duplicate_groups:

            # Identify the master episode. This could be either:
            # 1. An episode that already exists as a 'master' in the existing database
            # 2. The episode with the smallest ep_id in the group if no such 'master' exists in the database
            existing_master = next((ep for ep in group if any(ep.ep_id == master for master, _ in existing_combos)), None)
            master_episode = existing_master or min(group, key=lambda x: x.ep_id)

            master_info_dict = {
                'master': master_episode,
                'duplicates': []
            }

            for episode in group:

                # Skip if the episode is the same as the master episode
                if master_episode.ep_id == episode.ep_id:
                    continue

                # Skip if the (master, duplicate) combo already exists
                combination = (master_episode.ep_id, episode.ep_id)
                if combination in existing_combos:
                    continue

                # Determine if master is new, and adjust the index accordingly to fetch from correct similarity matrix
                master_is_new = False
                if new_ep_id_to_index:
                    master_is_new = master_episode.ep_id in new_ep_id_to_index

                # If master/episode are new, their index in 'name_similarities' and 'description_similarities' are different
                master_index = new_ep_id_to_index[master_episode.ep_id] if master_is_new else all_ep_id_to_index[master_episode.ep_id]

                if new_ep_id_to_index and not master_is_new:
                    episode_index = new_ep_id_to_index[episode.ep_id]
                else:
                    episode_index = all_ep_id_to_index[episode.ep_id]

                # Calculate similarity metrics
                # Adjust for the case where the master is not new
                if not master_is_new:
                    name_similarity = int(name_similarities[episode_index][master_index] * 100)
                    desc_similarity = int(description_similarities[episode_index][master_index] * 100)
                else:
                    name_similarity = int(name_similarities[master_index][episode_index] * 100)
                    desc_similarity = int(description_similarities[master_index][episode_index] * 100)

                dur_similarity = int(self.duration_similarity(master_episode.ep_duration_sec, episode.ep_duration_sec) * 100)
                overall_similarity = (name_similarity + desc_similarity + dur_similarity) // 3

                # Save the duplicate information for database insertion
                duplicate_info = {
                    'duplicate_episode': episode,
                    'name_similarity': name_similarity,
                    'desc_similarity': desc_similarity,
                    'dur_similarity': dur_similarity,
                    'overall_similarity': overall_similarity
                }

                master_info_dict['duplicates'].append(duplicate_info)

            if master_info_dict['duplicates']:
                new_potential_duplicates.append(master_info_dict)

        return new_potential_duplicates
    
    
    def save_new_potential_duplicates_to_db(self, new_potential_duplicates) -> None:
        '''Saves the identified potential duplicates to the database and prints out information for each master-duplicate pair.'''

        for master_info_dict in new_potential_duplicates:

            # Print master episode info
            master_info = f"{master_info_dict['master'].ep_id} - {master_info_dict['master'].ep_duration_sec} - {master_info_dict['master'].ep_name[:60]}"
            print(f"\n// {master_info}")

            for duplicate_info in master_info_dict['duplicates']:
                
                # Print duplicate episode info
                duplicate_info_str = f"({duplicate_info['name_similarity']}%, {duplicate_info['desc_similarity']}%, {duplicate_info['dur_similarity']}%) {duplicate_info['duplicate_episode'].ep_id} - {duplicate_info['duplicate_episode'].ep_duration_sec} - {duplicate_info['duplicate_episode'].ep_name[:60]}"
                print(duplicate_info_str)

                # Save the potential duplicate info to the database
                PotentialDuplicate.objects.get_or_create(
                    master_episode=master_info_dict['master'],
                    duplicate_episode=duplicate_info['duplicate_episode'],
                    defaults={
                        'name_similarity': duplicate_info['name_similarity'],
                        'desc_similarity': duplicate_info['desc_similarity'],
                        'dur_similarity': duplicate_info['dur_similarity'],
                        'overall_similarity': duplicate_info['overall_similarity']
                    }
                )


    def get_potential_episode_duplicates(self, mode='new', name_thresh=0.2, desc_thresh=0.6, dur_thresh=0.9) -> None:
        """
        Searches for potential duplicate episodes based on the given mode ('new' or 'all') and similarity thresholds.
        A threshold value of 1 indicates 100% similarity.
        """

        if mode == 'new':
            print(f"\nDUPLICATES: Searching for NEW potential duplicates..\n")
        else:
            print(f"\nDUPLICATES: Searching for ALL potential duplicates..\n")

        self.print_ram_usage("Start of Function")      

        # Fetch all (distinct) episodes which are being used in the Episode_Person table,
        # which is the source for the online live data on our website.
        all_episodes = list(Include_Episode.objects.filter(episode_person__id__isnull=False).distinct())

        self.print_ram_usage("After fetching episodes")

        # Create a mapping from episode ID to index for efficient lookup in later comparisons
        all_ep_id_to_index = {ep.ep_id: index for index, ep in enumerate(all_episodes)}

        new_episodes = None
        new_ep_id_to_index = None
        
        # Separate new episodes from all episodes if the mode is "new"
        if mode == 'new':
            date_today = datetime.now().date()
            new_episodes = [ep for ep in all_episodes if ep.scrape_date == date_today]
            new_ep_id_to_index = {ep.ep_id: index for index, ep in enumerate(new_episodes)}
            
            # Check if there are no new episodes today
            if not new_episodes:
                print("\nDUPLICATES: No new episodes for potential duplicate comparison\n")
                return

        # Import sklearn libraries here to monitor RAM usage
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity

        self.print_ram_usage("After sklearn import")

        # Use TF-IDF to convert episode names and descriptions into numerical vectors for text similarity analysis
        all_name_tfidf_matrix, all_description_tfidf_matrix = self.vectorize_episode_data(all_episodes)
        
        self.print_ram_usage("After TF-IDF vectorization")

        if mode == 'new':
            # Extract relevant (new) rows from the all_name_tfidf_matrix and all_description_tfidf_matrix for efficiency
            # This reduces the computational load when comparing only new episodes against all episodes.
            new_indices = [all_ep_id_to_index[ep.ep_id] for ep in new_episodes]
            new_name_tfidf_matrix = all_name_tfidf_matrix[new_indices]
            new_description_tfidf_matrix = all_description_tfidf_matrix[new_indices]

            # Compute pairwise cosine similarities to measure the angle between TF-IDF vectors of new and all episodes, ideal for text similarity.
            name_similarities = cosine_similarity(new_name_tfidf_matrix, all_name_tfidf_matrix)
            description_similarities = cosine_similarity(new_description_tfidf_matrix, all_description_tfidf_matrix)
        
        else:
            # Compute pairwise cosine similarities for all names and descriptions
            name_similarities, description_similarities = self.compute_similarities(all_name_tfidf_matrix, all_description_tfidf_matrix)

        self.print_ram_usage("After calculating cosine similarities")
        
        print()

        # Identify all potential duplicates based on similarity thresholds
        potential_duplicate_groups = self.identify_all_potential_duplicates(
            all_episodes, 
            name_similarities, 
            description_similarities,
            name_thresh=name_thresh, 
            desc_thresh=desc_thresh, 
            dur_thresh=dur_thresh,
            new_episodes=new_episodes,
            new_ep_id_to_index=new_ep_id_to_index
        )

        # Fetch all existing (master, duplicate) combinations from the database
        existing_combinations = set(PotentialDuplicate.objects.all().values_list('master_episode', 'duplicate_episode')
        )

        # Filter out existing duplicates and prepare new ones for database insertion
        new_potential_duplicates = self.filter_new_potential_duplicates(
            potential_duplicate_groups,
            existing_combinations,
            all_ep_id_to_index,
            name_similarities,
            description_similarities,
            new_ep_id_to_index=new_ep_id_to_index
        )

        if not new_potential_duplicates:
            print("DUPLICATES: No new potential duplicates found\n")
        else:
            total_new_duplicates = sum(len(master_info_dict['duplicates']) for master_info_dict in new_potential_duplicates)
            print(f"DUPLICATES: Inserting {total_new_duplicates} new potential duplicate entries into the database:")
            self.save_new_potential_duplicates_to_db(new_potential_duplicates)