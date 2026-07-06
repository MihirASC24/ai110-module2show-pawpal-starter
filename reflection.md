# PawPal+ Project Reflection

## 1. System Design
-Add pet with relevant info about pet
-Tell owner what tasks need to be done for pet
-Schedule activities for pet with constraints
**a. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

Classes:
-Owner
    -Attributes: name, preferences, calendar (list of Daily_Plans), list of Pets
    -Methods: 
        -add_plan(Daily_Plan): adds a Daily_Plan to calendar
        -remove_plan(): removes Daily_Plan
-Pet
    -Attributes: characteristics (Name, species, Task(list))
    -Methods:
        -addTask(Task): adds Task to list
        -removeTask(Task): removes Task from list
        -addPet(Pet)
        -removePet(Pet)
-Daily_plans
    -Attributes: day (int month, int day), dict (Task : time)
    -Methods: 
        addEvent(Task, int hour, int minute): Adds task at time, in consideration of priority
        removeEvent(Task): Removes task from daily plan
-Task
    -Attributes: Name, applicable Pets, time_needed(int hour, int minute), int priority

---

**b. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

Scheduled events were originally stored in a dict, with the key being the Task and the value being the time (hour) it was scheduled for. I re-keyed with hour so checking times would be easier. This gives a collision-check time of O(1). Additionally, multi-hour tasks can be represented.
---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
