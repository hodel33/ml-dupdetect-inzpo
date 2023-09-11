# Django imports
from django.db import models


class PotentialDuplicate(models.Model):
    master_episode = models.ForeignKey(Include_Episode, related_name='master_episodes', on_delete=models.CASCADE)
    duplicate_episode = models.ForeignKey(Include_Episode, related_name='duplicate_episodes', on_delete=models.CASCADE)
    name_similarity = models.IntegerField(null=True, blank=True)
    desc_similarity = models.IntegerField(null=True, blank=True)
    dur_similarity = models.IntegerField(null=True, blank=True)
    overall_similarity = models.IntegerField(null=True, blank=True)
    date_added = models.DateField(auto_now_add=True)
    is_duplicate = models.BooleanField(null=True, default=None)
    switch_episode = models.BooleanField(default=False)

    class Meta:
        unique_together = ('master_episode', 'duplicate_episode')
        verbose_name_plural = "* Potential Duplicates *"
        app_label = 'core'
    
    def __str__(self) -> str:
        return f"{self.master_episode.ep_name} - {self.duplicate_episode.ep_name}"
    
    def save(self, *args, **kwargs):

        super(PotentialDuplicate, self).save(*args, **kwargs)

        # Check if is_duplicate is marked as True
        if self.is_duplicate is True:

            # Decide which episode to exclude based on switch_episode
            if self.switch_episode:
                episode_to_exclude = self.master_episode
            else:
                episode_to_exclude = self.duplicate_episode

            # Move the episode to Exclude_Episode
            Exclude_Episode.objects.update_or_create(
                ep_id=episode_to_exclude.ep_id,
                defaults={
                    'show': episode_to_exclude.show,
                    'ep_name': episode_to_exclude.ep_name,
                    'ep_description': episode_to_exclude.ep_description,
                    'ep_duration_sec': episode_to_exclude.ep_duration_sec,
                    'language': episode_to_exclude.language,
                    'ep_url': episode_to_exclude.ep_url,
                    'image_cover_url': episode_to_exclude.image_cover_url,
                    'release_date': episode_to_exclude.release_date,
                    'scrape_date': episode_to_exclude.scrape_date,
                    'scrape_guests': episode_to_exclude.scrape_guests
                }
            )

            # Delete the episode from Include_Episode table
            episode_to_exclude.delete()