# Django imports
from core.models import PotentialDuplicate
from django.contrib import admin
from django.db.models import Count, Max, Subquery, OuterRef

from django.utils.html import format_html

      
@admin.register(PotentialDuplicate)
class PotentialDuplicateAdmin(admin.ModelAdmin):

    list_display = ('name_sim', 'desc_sim', 'dur_sim', 'master_episode_link', 'duplicate_episode_link', 'date_added', 'highlight_group', 'switch_episode', 'is_duplicate')
    list_editable = ('is_duplicate', 'switch_episode')
    list_filter = ('is_duplicate',)
    list_display_links = None  # # Disable linking to the detail view for all fields

    def name_sim(self, obj):
        return obj.name_similarity
    name_sim.short_description = 'Nam'

    def desc_sim(self, obj):
        return obj.desc_similarity
    desc_sim.short_description = 'Des'

    def dur_sim(self, obj):
        return obj.dur_similarity
    dur_sim.short_description = 'Dur'

    # Generate a clickable link for the master episode
    def master_episode_link(self, obj):
        return format_html('<a href="{url}" target="_blank">{name}</a>', url=obj.master_episode.ep_url, name=obj.master_episode)
    master_episode_link.short_description = 'Master Episode'

    # Generate a clickable link for the duplicate episode
    def duplicate_episode_link(self, obj):
        return format_html('<a href="{url}" target="_blank">{name}</a>', url=obj.duplicate_episode.ep_url, name=obj.duplicate_episode)
    duplicate_episode_link.short_description = 'Duplicate Episode'

    def get_actions(self, request):
        # Get the default actions and remove the delete_selected action
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions
    
    # Disable the 'add' functionality in the admin interface
    def has_add_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        # Customize the query to annotate each row with additional information
        qs = super().get_queryset(request)

        # Annotate each master episode with max similarity score and duplicate count
        annotations_for_master = PotentialDuplicate.objects.filter(
            master_episode=OuterRef('master_episode')
        ).values('master_episode').annotate(
            max_similarity=Max('overall_similarity'),
            duplicate_count_for_master=Count('master_episode')
        ).values('max_similarity', 'duplicate_count_for_master')

        # Apply annotations to the main queryset
        qs = qs.annotate(
            max_group_similarity=Subquery(annotations_for_master.values('max_similarity')[:1]),
            duplicate_count=Subquery(annotations_for_master.values('duplicate_count_for_master')[:1])
        )

        # Order by max_group_similarity and then by overall_similarity of each entry.
        return qs.order_by('-max_group_similarity', '-overall_similarity')
        
    # Highlight entries with more than one duplicate
    def highlight_group(self, obj):
        if obj.duplicate_count > 1:
            return format_html('<span style="font-size: 18px; font-weight: bold; color: #70bf2b;">&#10003;</span>')
        else:
            return ""
    highlight_group.short_description = 'GROUP'
    highlight_group.allow_tags = True