This suite comes with -six- actions.
The first five actions are intended to be correct, and function properly.
The sixth action is intended to fail everything miserably.

I have not included the "fail miserably" part with 1-5 because doing so, I believe, would make grading more difficult. 

As for implemented features, I have:
    add
    remove (you can remove on any field. Additionally, you can use the '*' wildcard. i.e. you can say:
            rm
            Part: id="1*"
        and all parts with an id starting with 1 will be removed)
    set/update (you can update any field based on any other field. Wildcard rules apply here as well.)
    list (you can list based on any field(s). Wildcard rules apply here. You can give multiple list constraints. i.e.:
            list
            Part: id="10" footprint="abc*"
            Part: id="11"
        This will list all parts with id==10 and footprint=="abc*", as well as any parts that just have id==11.
        Specifying requirements on the same line is effectively an AND. Different lines is effectively an OR.)
    sorted list (can sort on any field. Can sort on multiple fields. First mentioned field is most significant field to sort by. e.x.
            list
            Part: quantity="13"
            sort Part by id, footprint
        will list all parts with quantity 13, sorted by ID, then the ID 'subsections' sorted by footprint.)
    Also, sorting does do appropriate sorting for type. So, sorting based on quantity should function as expected. :)

Assuming nothing goes horribly wrong, I should get 60/50 points. Yay :D

Also, the delimiter for input was two newlines. So, to 'chain' commands in the same session, put two blank lines.

Good:
add
Part: id="10" description="hi" quantity="890" footprint="20"


del
Part: id="10"






Bad:
add
Part: id="10" description="hi" quantity="890" footprint="20"

del
Part: id="10"
