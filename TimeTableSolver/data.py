import hard_constraints as hc
import general_info as gi
import math
import copy


class Course:
    def __init__(self, code, name, student_amount, contact_hours, lecturers, curricula):
        self.code = code
        self.name = name
        self.student_amount = int(student_amount)
        self.contact_hours = contact_hours
        self.course_hours = math.ceil(contact_hours*0.8)
        self.lecturers = lecturers
        self.curricula = curricula
        self.course_events = []


class Lecturer:
    def __init__(self, ugent_id, first_name, last_name):
        self.ugent_id = ugent_id
        self.first_name = first_name
        self.last_name = last_name
        self.occupied_time_slots = set()

    def add_occupied_time_slot(self, time_slot_number):
        if time_slot_number in self.occupied_time_slots:
            return False
        self.occupied_time_slots.add(time_slot_number)
        return True

    def remove_occupied_time_slot(self, time_slot_number):
        self.occupied_time_slots.discard(time_slot_number)

    def contains_time_slot(self, time_slot_number):
        return time_slot_number in self.occupied_time_slots


class Curriculum:
    def __init__(self, code, mt1, home_site):
        self.code = code
        self.mt1 = mt1
        self.home_site = home_site
        self.occupied_time_slots = set()

    def add_occupied_time_slot(self, time_slot_number):
        if time_slot_number in self.occupied_time_slots:
            return False
        self.occupied_time_slots.add(time_slot_number)
        return True

    def remove_occupied_time_slot(self, time_slot_number):
        self.occupied_time_slots.discard(time_slot_number)

    def contains_time_slot(self, time_slot_number):
        return time_slot_number in self.occupied_time_slots


class Site:
    def __init__(self, code, name, x_coord, y_coord, class_rooms):
        self.code = code
        self.name = name
        self.x_coord = x_coord
        self.y_coord = y_coord
        self.class_rooms = class_rooms


class ClassRoom:
    def __init__(self, fi_number, name, capacity, site_id):
        self.fi_number = fi_number
        self.name = name
        self.capacity = int(capacity)
        self.site_id = site_id


class CourseEvent:
    def __init__(self, course_code, lecturers, student_amount, curricula, event_number):
        self.course_code = course_code
        self.lecturers = lecturers
        self.student_amount = student_amount
        self.curricula = curricula
        self.event_number = event_number
        self.assigned_lecturer = None

    def set_assigned_lecturer(self, ugent_id):
        if self.assigned_lecturer is None:
            self.assigned_lecturer = copy.deepcopy(ugent_id)
            return True
        return False

    def remove_assigned_lecturer(self):
        self.assigned_lecturer = None


class TimeTable:

    def __init__(self, timetable, occupied_positions, empty_positions, offset):
        self.timetable = timetable
        self.occupied_positions = occupied_positions
        self.empty_positions = empty_positions
        self.offset = offset

    def assign_course_to_position(self, course_event, position):
        """
        This function will assign a course_event to a specific position in the time table.
        :param course_event: instance of CourseEvent, the course event that will be scheduled.
        :param position: (fi_number, time_slot)
        :return: True if the event is successfully scheduled, False otherwise
        """

        if self.timetable[position] is not None:
            self.remove_course_from_position(position)

        if course_event is None:
            return False

        self.timetable[position] = course_event
        course = gi.courses_dict[course_event.course_code]
        room_fi_number = position[0]
        time_slot = position[1] + 40 * self.offset

        for curriculum_code in course.curricula:
            curriculum = gi.curricula_dict[curriculum_code]
            # adding the time_slot to the list of occupied time_slots
            curriculum.add_occupied_time_slot(time_slot)

        # get a lecturer
        assigned_lecturer = None
        for ugent_id in course_event.lecturers:
            lecturer = gi.lecturers_dict[ugent_id]
            if not hc.lecturer_is_occupied_in_time_slot(lecturer, time_slot):
                assigned_lecturer = lecturer
                break

        assigned_lecturer.add_occupied_time_slot(time_slot)
        course_event.set_assigned_lecturer(assigned_lecturer.ugent_id)

        course.course_hours -= 1
        self.occupied_positions.append(position)
        try:
            self.empty_positions.remove(position)
        except ValueError:
            # event got swapped, so is not part of events.
            return

    def remove_course_from_position(self, position):
        """
        This function will remove a courseEvent from the timetable.
        :param position: (fi_number, time_slot)
        :return: True if the removal is successful, False otherwise
        """
        fi_number = position[0]
        time_slot = position[1] + 40 * self.offset
        if self.timetable[position] is not None:
            course_event = self.timetable[position]
            self.timetable[position] = None
            self.empty_positions.append(position)
            self.occupied_positions.remove(position)
            course = gi.courses_dict[course_event.course_code]
            course.course_hours += 1

            # remove the time_slot from the occupied time_sot list from every curriculum
            for curriculum_code in course.curricula:
                curriculum = gi.curricula_dict[curriculum_code]
                curriculum.remove_occupied_time_slot(time_slot)

            ugent_id = course_event.assigned_lecturer
            lecturer = gi.lecturers_dict[ugent_id]
            lecturer.remove_occupied_time_slot(time_slot)
            course_event.remove_assigned_lecturer()

            return course_event
        return False

    def update_offset(self, offset):
        """
        This function will change the new offset and make sure that all relevant values get updated.
        Warning! only use this function when copying a timetable to use as the base timetable for the new week.
        """
        self.offset = offset

        # iterate over all non None values in the dictionary
        # update all occupied time_slot sets
        for course_event in self.timetable.values():
            if course_event is not None:
                assigned_lecturer = gi.lecturers_dict[course_event.assigned_lecturer]
                # update occupied time slots for the lecturer
                new_time_slots = set()
                for occupied_time_slot in assigned_lecturer.occupied_time_slots:
                    new_time_slots.add(occupied_time_slot % 40 + offset*40)
                assigned_lecturer.occupied_time_slots.union(new_time_slots)
                # update occupied time slots for the curricula
                for curriculum_code in course_event.curricula:
                    curriculum = gi.curricula_dict[curriculum_code]
                    new_time_slots = set()
                    for occupied_time_slot in curriculum.occupied_time_slots:
                        new_time_slots.add(occupied_time_slot % 40 + offset*40)
                    curriculum.occupied_time_slots.union(new_time_slots)
