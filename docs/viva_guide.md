# CampusConnect viva guide

- **MVT:** models store data, views handle requests/logic, templates render HTML.
- **Model vs form:** a model describes database data; a form validates user input before saving it.
- **CBVs:** `ListView`, `DetailView`, `CreateView`, `UpdateView`, and `DeleteView` reduce repeated CRUD code. `LoginRequiredMixin` protects a view; `UserPassesTestMixin` checks creator/staff ownership.
- **Sessions vs cookies:** sessions keep server-side data such as visit counters and recent event IDs; cookies keep small browser values such as the preferred category.
- **Search:** `Q` objects combine title, organizer, description, and location searches. GET is appropriate because it does not change data and keeps a shareable URL.
- **State changes:** RSVP, favorites, comments, and deletes use POST plus CSRF tokens because they change server data.
- **Uploads:** `ImageField` stores a media-file path; static files are app assets distributed with the project.
- **Constraints:** `ForeignKey` is many-to-one; `OneToOneField` gives each user one profile. `related_name` makes reverse queries readable. `UniqueConstraint` stops duplicate RSVPs/favorites at the database level.
- **Authorization:** hiding an edit button is not security. The update/delete view checks the creator or staff user on the server.
- **Fixtures/tests:** fixtures load repeatable demo records. `TestCase` creates an isolated test database so tests do not alter development data.

Likely questions: Why POST for RSVP? To prevent accidental state changes from a link. How is capacity enforced? The RSVP view checks active attendance inside a transaction. How does password reset work? Django generates a time-limited token and writes the email to the development console. Why use `select_related`? It reduces repeated queries for related event/category/user data.
