from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from hr.models import PerformanceAspect


class Command(BaseCommand):
    help = 'Seeds the 16 default performance aspects from the GEN 79 form'

    def handle(self, *args, **kwargs):

        # Get the first superuser to assign as creator
        admin_user = User.objects.filter(is_superuser=True).first()

        aspects = [
            {
                'label': 'Foresight',
                'outstanding_description': 'Anticipates problems and develops solution in advance',
                'unsatisfactory_description': 'Grapples with problems after they arise',
                'order': 1,
            },
            {
                'label': 'Penetration',
                'outstanding_description': 'Gets straight to the roots of a problem',
                'unsatisfactory_description': 'Seldom sees below the surface of a problem',
                'order': 2,
            },
            {
                'label': 'Judgement',
                'outstanding_description': 'His decisions or proposals are consistently sound',
                'unsatisfactory_description': 'Poor perception of relative merits or feasibility in most situations',
                'order': 3,
            },
            {
                'label': 'Expression on Paper',
                'outstanding_description': 'Always cogent, clear and well set out',
                'unsatisfactory_description': 'Ambiguous, clamsy and obscure',
                'order': 4,
            },
            {
                'label': 'Oral Expression',
                'outstanding_description': 'Puts his points across convincingly and concisely',
                'unsatisfactory_description': 'Finds difficulty in expressing himself',
                'order': 5,
            },
            {
                'label': 'Numerical Ability',
                'outstanding_description': 'Accurate in the use and interpretation of figures',
                'unsatisfactory_description': 'Gets confused with figures',
                'order': 6,
            },
            {
                'label': 'Relations with Colleagues',
                'outstanding_description': 'Sensitive to other peoples feelings, tactful and understanding of personal problems',
                'unsatisfactory_description': 'Ignores or belittles other peoples feelings; intolerant, does not earn respect',
                'order': 7,
            },
            {
                'label': 'Relations with the Public',
                'outstanding_description': 'Exceptionally effective in dealing with people of all types',
                'unsatisfactory_description': 'Tactless and cannot deal with the public',
                'order': 8,
            },
            {
                'label': 'Acceptance of Responsibility',
                'outstanding_description': 'Seeks and accepts responsibility at all times',
                'unsatisfactory_description': 'Avoids responsibility, will pass it on when possible',
                'order': 9,
            },
            {
                'label': 'Reliability under Pressure',
                'outstanding_description': 'Performs competently under pressure',
                'unsatisfactory_description': 'Easily thrown off balance, not reliable even under normal circumstances',
                'order': 10,
            },
            {
                'label': 'Drive and Determination',
                'outstanding_description': 'Wholehearted application to tasks; determined to carry task through to completion',
                'unsatisfactory_description': 'Lacks determination, easily baulked by minor setbacks',
                'order': 11,
            },
            {
                'label': 'Application of Professional/Technical Knowledge',
                'outstanding_description': 'Highly proficient in the practical application of professional/technical knowledge',
                'unsatisfactory_description': 'Deficient in applying professional technical knowledge to practical issues',
                'order': 12,
            },
            {
                'label': 'Management of Staff',
                'outstanding_description': 'Organises and inspires staff to give of their best',
                'unsatisfactory_description': 'Inefficient in the use of staff; engenders low morale',
                'order': 13,
            },
            {
                'label': 'Output of Work',
                'outstanding_description': 'Gets a great deal done within a set of time',
                'unsatisfactory_description': 'Stoppish in output',
                'order': 14,
            },
            {
                'label': 'Quality of Work',
                'outstanding_description': 'Maintains very high standards; work is virtually error proof',
                'unsatisfactory_description': 'Maintains consistently low standards, constant complaint',
                'order': 15,
            },
            {
                'label': 'Punctuality',
                'outstanding_description': 'Regularly punctual at work',
                'unsatisfactory_description': 'No regard for punctuality',
                'order': 16,
            },
        ]

        created_count = 0
        skipped_count = 0

        for aspect_data in aspects:
            # get_or_create prevents duplicates if command is run twice
            # It returns (object, created) — created is True if new, False if existing
            aspect, created = PerformanceAspect.objects.get_or_create(
                label=aspect_data['label'],
                defaults={
                    'outstanding_description': aspect_data['outstanding_description'],
                    'unsatisfactory_description': aspect_data['unsatisfactory_description'],
                    'order': aspect_data['order'],
                    'created_by': admin_user,
                }
            )
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"  Created: {aspect.label}"))
            else:
                skipped_count += 1
                self.stdout.write(self.style.WARNING(f"  Skipped (already exists): {aspect.label}"))

        self.stdout.write(
            self.style.SUCCESS(
                f"\nDone! {created_count} aspects created, {skipped_count} skipped."
            )
        )