from rest_framework import serializers
from .models import Tasks

class TasksSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tasks
        fields = '__all__'
        read_only_fields = ['author']

    def validate_title(self, value):
        if not value.strip():
            raise serializers.ValidationError('Tasks title cannot be empty')
        return value

    def validate_content(self, value):
        if len(value) < 10:
            raise serializers.ValidationError('Tasks content cannot be less than 10 characters')
        return value
